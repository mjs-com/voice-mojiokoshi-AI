"""Gemini LLM 整形エンジン

Google Gemini API（google-genai パッケージ）を使用して、
音声文字起こしの生テキストをフィラー除去・句読点付与・書き言葉化などの整形処理を行う。

429 レート制限エラー対策（Google公式ドキュメント準拠）:
  - 切り捨て指数バックオフ + ジッター（ランダムな揺らぎ）
  - 初回待機1秒 → 2秒 → 4秒 → 8秒...（最大60秒）
  - サーバー指定の retryDelay がある場合はそちらを優先
  - 同一モデルで最大5回リトライ
  - すべて失敗したら代替モデルにフォールバック

参考:
  - https://cloud.google.com/storage/docs/retry-strategy?hl=ja
  - https://ai.google.dev/gemini-api/docs/rate-limits
  - https://cloud.google.com/blog/products/ai-machine-learning/learn-how-to-handle-429-resource-exhaustion-errors-in-your-llms
"""

import re
import time
import random

from google import genai

from .base import LLMFormatter


# フォールバック用モデルリスト（上から順に試す）
FALLBACK_MODELS = [
    "gemini-2.0-flash",
    "gemini-1.5-flash",
]

# 指数バックオフ設定（Google公式推奨値ベース）
INITIAL_DELAY = 1.0       # 初回待機（秒）
MAX_DELAY = 60.0           # 最大待機（秒）
DELAY_MULTIPLIER = 2.0     # 乗数
MAX_RETRIES = 5             # 最大リトライ回数


class GeminiFormatter(LLMFormatter):
    """Google Gemini API を使用するLLM整形エンジン"""

    def __init__(self, api_key: str, model: str = "gemini-2.0-flash-lite"):
        self._api_key = api_key
        self._model_name = model
        self._client = genai.Client(api_key=api_key)

    def format_text(self, raw_text: str, prompt_template: str) -> str:
        """生テキストをGeminiで整形する

        429エラー時は指数バックオフ＋代替モデルフォールバックを行う。
        """
        full_prompt = prompt_template.replace("{raw_text}", raw_text)

        # 1) デフォルトモデルで指数バックオフ付きリトライ
        result = self._send_with_exponential_backoff(full_prompt, self._model_name)
        if result is not None:
            return result

        # 2) フォールバックモデルで試行
        for fallback in FALLBACK_MODELS:
            if fallback == self._model_name:
                continue
            print(f"   ↪ 代替モデル {fallback} で再試行...")
            result = self._send_with_exponential_backoff(full_prompt, fallback)
            if result is not None:
                return result

        # 3) すべて失敗
        print("   ⚠️ すべてのモデルでAPI制限に達しました。生テキストをそのまま出力します。")
        print("   💡 ヒント: 数分待ってから再度お試しください。")
        print("      無料枠の制限: RPM=15（1分あたり15回）、RPD=1000（1日あたり1000回）")
        return raw_text

    def _send_with_exponential_backoff(self, prompt: str, model: str) -> str | None:
        """指数バックオフ＋ジッターでリトライ送信する。

        Google公式ドキュメント準拠:
        - 初回待機: 1秒
        - 乗数: 2.0（1→2→4→8→16→32→60秒）
        - ジッター: 待機時間の ±50% のランダム揺らぎ
        - 最大待機: 60秒
        - サーバー指定の retryDelay がある場合はそちらを優先

        Returns:
            成功時: 整形済みテキスト
            全リトライ失敗時: None
        """
        delay = INITIAL_DELAY

        for attempt in range(MAX_RETRIES + 1):
            try:
                response = self._client.models.generate_content(
                    model=model,
                    contents=prompt,
                )
                return response.text.strip()

            except Exception as e:
                error_msg = str(e)

                # --- 429 レート制限 ---
                if "429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg:
                    if attempt >= MAX_RETRIES:
                        print(f"   ❌ {model}: {MAX_RETRIES}回リトライしましたが制限解除されません。")
                        return None

                    # サーバー指定の待機時間があればそちらを使う
                    server_delay = self._parse_retry_delay(error_msg)
                    if server_delay > 0:
                        wait = server_delay
                    else:
                        # 指数バックオフ + ジッター（±50%のランダム揺らぎ）
                        jitter = delay * random.uniform(0.5, 1.5)
                        wait = min(jitter, MAX_DELAY)

                    print(f"   ⏳ API制限 ({model}) → {wait:.0f}秒後にリトライ "
                          f"({attempt + 1}/{MAX_RETRIES})")
                    time.sleep(wait)

                    # 次回の基本遅延を増やす（指数増加）
                    delay = min(delay * DELAY_MULTIPLIER, MAX_DELAY)
                    continue

                # --- APIキーエラー（リトライしない）---
                elif "API_KEY" in error_msg.upper() or "401" in error_msg:
                    print("   ❌ APIキーが無効です。設定画面でAPIキーを確認してください。")
                    return None

                # --- モデル不在（リトライしない）---
                elif "404" in error_msg or "not found" in error_msg.lower():
                    print(f"   ❌ モデル '{model}' が見つかりません。")
                    return None

                # --- その他のエラー（リトライしない）---
                else:
                    print(f"   ❌ LLMエラー ({model}): {e}")
                    return None

        return None

    @staticmethod
    def _parse_retry_delay(error_msg: str) -> float:
        """エラーメッセージからサーバー指定のリトライ待機秒数を抽出する。

        Gemini API は 'Please retry in 42.327s' や 'retryDelay': '42s'
        のような形で待ち時間を教えてくれる。

        Returns:
            抽出できた場合: 秒数（余裕を+2秒追加）
            抽出できなかった場合: 0（呼び出し元で指数バックオフを使う）
        """
        # 'retry in XX.XXXs' パターン
        match = re.search(r'retry in (\d+(?:\.\d+)?)s', error_msg, re.IGNORECASE)
        if match:
            return float(match.group(1)) + 2

        # 'retryDelay': 'XXs' パターン
        match = re.search(r"retryDelay['\"]?\s*[:=]\s*['\"]?(\d+)", error_msg)
        if match:
            return float(match.group(1)) + 2

        # 見つからなければ0を返し、呼び出し元の指数バックオフに任せる
        return 0

    def get_name(self) -> str:
        return f"Gemini ({self._model_name})"
