"""クレデンシャル管理モジュール

APIキーなどの機密情報をWindows Credential Manager（資格情報マネージャー）に
安全に保存・取得する。

保存先: Windows 資格情報マネージャー > Windows 資格情報
  → 暗号化されてWindowsユーザーアカウントに紐づくため、
     config.jsonに平文で保存するより安全。
  → アプリを配布しても、各ユーザーのローカル環境に保存される。
"""

import keyring

# アプリ識別子（Credential Managerでの表示名）
SERVICE_NAME = "指いらず"

# 保存キーの定義
KEY_GEMINI_API = "gemini_api_key"
KEY_OPENAI_API = "openai_api_key"
KEY_CLAUDE_API = "claude_api_key"


def save_api_key(provider: str, api_key: str) -> None:
    """APIキーをCredential Managerに保存する

    Args:
        provider: プロバイダー名（"gemini", "openai", "claude"）
        api_key: 保存するAPIキー
    """
    key_name = _get_key_name(provider)
    keyring.set_password(SERVICE_NAME, key_name, api_key)


def get_api_key(provider: str) -> str | None:
    """Credential ManagerからAPIキーを取得する

    Args:
        provider: プロバイダー名（"gemini", "openai", "claude"）

    Returns:
        APIキー。未設定の場合はNone。
    """
    key_name = _get_key_name(provider)
    return keyring.get_password(SERVICE_NAME, key_name)


def delete_api_key(provider: str) -> None:
    """Credential ManagerからAPIキーを削除する

    Args:
        provider: プロバイダー名（"gemini", "openai", "claude"）
    """
    key_name = _get_key_name(provider)
    try:
        keyring.delete_password(SERVICE_NAME, key_name)
    except keyring.errors.PasswordDeleteError:
        pass  # 存在しない場合は無視


def has_api_key(provider: str) -> bool:
    """APIキーが設定済みかどうかを返す"""
    return get_api_key(provider) is not None


def prompt_api_key(provider: str) -> str | None:
    """コンソールでAPIキーの入力を求め、Credential Managerに保存する

    Args:
        provider: プロバイダー名

    Returns:
        入力されたAPIキー。スキップされた場合はNone。
    """
    provider_names = {
        "gemini": "Google Gemini",
        "openai": "OpenAI",
        "claude": "Anthropic Claude",
    }
    display_name = provider_names.get(provider, provider)

    print(f"\n  🔑 {display_name} APIキーの設定")
    print(f"     APIキーはWindows資格情報マネージャーに安全に保存されます。")

    if provider == "gemini":
        print(f"     取得先: https://aistudio.google.com/app/apikey")

    api_key = input(f"\n     APIキーを入力（スキップするにはEnter）: ").strip()

    if api_key:
        save_api_key(provider, api_key)
        print(f"     ✅ APIキーをWindows資格情報マネージャーに保存しました。")
        return api_key
    else:
        print(f"     ⏭️  スキップしました。後から設定画面で登録できます。")
        return None


def _get_key_name(provider: str) -> str:
    """プロバイダー名からCredential Managerのキー名を取得する"""
    mapping = {
        "gemini": KEY_GEMINI_API,
        "openai": KEY_OPENAI_API,
        "claude": KEY_CLAUDE_API,
    }
    return mapping.get(provider, f"{provider}_api_key")
