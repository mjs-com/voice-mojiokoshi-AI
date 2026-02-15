"""設定管理モジュール

config.json の読み書きを行う。
存在しない場合はデフォルト設定で自動生成する。
"""

import json
import os
import copy

# デフォルト設定
DEFAULT_CONFIG = {
    "hotkeys": {
        "push_to_talk": "right alt",
        "hands_free": "f2",
    },
    "suppress_hotkeys": True,
    "stt": {
        "engine": "google_free",
    },
    "llm": {
        "provider": "gemini",
        "model": "gemini-2.0-flash-lite",
        # APIキーはここに保存しない（Windows Credential Managerで管理）
    },
    "prompt": (
        "あなたは音声文字起こしの整形アシスタントです。\n"
        "以下の音声文字起こし生テキストを、そのまま使える自然な日本語の書き言葉に整形してください。\n"
        "\n"
        "【絶対に守るルール】\n"
        "1. 必ず句読点を入れること。読点「、」は意味の区切りに、句点「。」は文末に必ず付けること。"
        "句読点のない文は絶対に出力しないこと。\n"
        "2. 「あー」「えーと」「まあ」「なんか」「えー」「うーん」などのフィラー（言い淀み）を完全に削除する。\n"
        "3. 適切な位置で改行・段落分けを行う。\n"
        "4. 話し言葉を自然な書き言葉に変換する（意味は変えない）。\n"
        "5. 明らかな言い間違いや重複表現を修正する。\n"
        "6. 漢字変換の誤りを文脈から推測して修正する。\n"
        "7. 元の発話の意図・内容を一切変えない（要約しない、情報を追加しない）。\n"
        "\n"
        "【句読点の例】\n"
        "入力: 明日の会議なんですけど13時からに変更してほしいんですがよろしくお願いします\n"
        "出力: 明日の会議ですが、13時からに変更していただけますでしょうか。よろしくお願いいたします。\n"
        "\n"
        "【出力】\n"
        "整形後のテキストのみを出力してください。説明や補足は一切不要です。\n"
        "\n"
        "【音声文字起こし生テキスト】\n"
        "{raw_text}"
    ),
    "auto_start": False,
}


class Settings:
    """設定管理クラス"""

    def __init__(self, config_path: str = "config.json"):
        self._config_path = config_path
        self._config: dict = self._load()

    @property
    def config(self) -> dict:
        """現在の設定辞書を返す"""
        return self._config

    def _load(self) -> dict:
        """config.json を読み込む。存在しない場合はデフォルトを使用。"""
        if os.path.exists(self._config_path):
            try:
                with open(self._config_path, "r", encoding="utf-8") as f:
                    saved = json.load(f)
                # デフォルト設定をベースに、保存済み設定で上書き
                config = copy.deepcopy(DEFAULT_CONFIG)
                self._deep_merge(config, saved)
                return config
            except (json.JSONDecodeError, IOError) as e:
                print(f"⚠️  設定ファイルの読み込みに失敗しました: {e}")
                print("   デフォルト設定を使用します。")
                return copy.deepcopy(DEFAULT_CONFIG)
        else:
            # 初回起動: デフォルト設定でconfig.jsonを生成
            config = copy.deepcopy(DEFAULT_CONFIG)
            self._save(config)
            return config

    def _save(self, config: dict | None = None) -> None:
        """設定をconfig.jsonに保存する"""
        if config is None:
            config = self._config
        try:
            with open(self._config_path, "w", encoding="utf-8") as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
        except IOError as e:
            print(f"⚠️  設定ファイルの保存に失敗しました: {e}")

    def save(self) -> None:
        """現在の設定を保存する"""
        self._save()

    def get(self, key: str, default=None):
        """設定値を取得する"""
        return self._config.get(key, default)

    def set(self, key: str, value) -> None:
        """設定値を更新する"""
        self._config[key] = value

    @staticmethod
    def _deep_merge(base: dict, override: dict) -> None:
        """辞書を再帰的にマージする（baseをoverrideで上書き）"""
        for key, value in override.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                Settings._deep_merge(base[key], value)
            else:
                base[key] = value
