"""プロンプトプリセット管理モジュール

prompts.json からプリセット一覧を読み込み、IDで本文を取得する。
ファイルが無い場合は組み込みのデフォルトプリセットを使用する。
"""

import json
import os

# アプリのルートディレクトリ（main.py がある場所）
_APP_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_PROMPTS_PATH = os.path.join(_APP_ROOT, "prompts.json")

# 組み込みデフォルト（prompts.json が無い場合用）
_BUILTIN_PRESETS = [
    {
        "id": "default",
        "name": "標準（句読点・フィラー除去）",
        "body": (
            "あなたは音声文字起こしの整形アシスタントです。\n"
            "以下の音声文字起こし生テキストを、そのまま使える自然な日本語の書き言葉に整形してください。\n\n"
            "【絶対に守るルール】\n"
            "1. 必ず句読点を入れること。読点「、」は意味の区切りに、句点「。」は文末に必ず付けること。"
            "句読点のない文は絶対に出力しないこと。\n"
            "2. 「あー」「えーと」「まあ」「なんか」などのフィラーを完全に削除する。\n"
            "3. 適切な位置で改行・段落分けを行う。\n"
            "4. 話し言葉を自然な書き言葉に変換する（意味は変えない）。\n"
            "5. 元の発話の意図・内容を一切変えない。\n\n"
            "【出力】\n整形後のテキストのみを出力してください。\n\n"
            "【音声文字起こし生テキスト】\n{raw_text}"
        ),
    },
]


def get_preset_list() -> list[dict]:
    """プリセット一覧を返す。各要素は {"id": str, "name": str, "body": str}"""
    if os.path.exists(_PROMPTS_PATH):
        try:
            with open(_PROMPTS_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
            presets = data.get("presets", [])
            if presets:
                return presets
        except (json.JSONDecodeError, IOError):
            pass
    return _BUILTIN_PRESETS


def get_preset_by_id(preset_id: str) -> dict | None:
    """ID に一致するプリセットを返す。無ければ None"""
    for p in get_preset_list():
        if p.get("id") == preset_id:
            return p
    return None


def get_preset_body(preset_id: str) -> str:
    """ID に一致するプリセットの本文を返す。無ければ空文字"""
    p = get_preset_by_id(preset_id)
    return p.get("body", "") if p else ""


def get_preset_names() -> list[str]:
    """プリセットの表示名のリストを返す（設定画面のコンボボックス用）"""
    return [p.get("name", "") for p in get_preset_list()]


def get_preset_body_by_name(name: str) -> str:
    """表示名に一致するプリセットの本文を返す。無ければ空文字"""
    for p in get_preset_list():
        if p.get("name") == name:
            return p.get("body", "")
    return ""


def get_preset_name_matching_body(body: str) -> str | None:
    """本文が一致するプリセットの表示名を返す。一致がなければ None"""
    body_stripped = (body or "").strip()
    if not body_stripped:
        return None
    for p in get_preset_list():
        if (p.get("body") or "").strip() == body_stripped:
            return p.get("name")
    return None
