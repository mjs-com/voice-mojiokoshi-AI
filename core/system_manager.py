"""システム管理モジュール

PC起動時の自動起動（スタートアップ登録）を管理する。
Windowsスタートアップフォルダにショートカットを配置する方式。
"""

import os
import sys


def get_startup_folder() -> str:
    """Windowsスタートアップフォルダのパスを返す"""
    return os.path.join(
        os.environ.get("APPDATA", ""),
        "Microsoft", "Windows", "Start Menu", "Programs", "Startup"
    )


def get_shortcut_path() -> str:
    """スタートアップに配置するショートカットのパスを返す"""
    return os.path.join(get_startup_folder(), "指いらず.bat")


def is_auto_start_enabled() -> bool:
    """自動起動が有効かどうかを返す"""
    return os.path.exists(get_shortcut_path())


def enable_auto_start() -> None:
    """PC起動時の自動起動を有効にする

    スタートアップフォルダにbatファイルを作成し、
    main.pyを起動するようにする。
    """
    app_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    main_py = os.path.join(app_dir, "main.py")
    python_exe = sys.executable

    bat_content = f'@echo off\ncd /d "{app_dir}"\nstart /min "" "{python_exe}" "{main_py}"\n'

    shortcut_path = get_shortcut_path()
    try:
        with open(shortcut_path, "w", encoding="utf-8") as f:
            f.write(bat_content)
        print(f"  ✅ 自動起動を有効にしました: {shortcut_path}")
    except IOError as e:
        print(f"  ⚠️ 自動起動の設定に失敗しました: {e}")


def disable_auto_start() -> None:
    """PC起動時の自動起動を無効にする"""
    shortcut_path = get_shortcut_path()
    try:
        if os.path.exists(shortcut_path):
            os.remove(shortcut_path)
            print(f"  ✅ 自動起動を無効にしました")
    except IOError as e:
        print(f"  ⚠️ 自動起動の解除に失敗しました: {e}")
