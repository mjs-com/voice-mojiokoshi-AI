"""出力モジュール

整形済みテキストをカーソル位置に直接挿入する。
テキストボックスが選択されていない場合のみ、
フォールバックとしてポップアップを表示する。

テキストボックスの判定はWin32 API (GetGUIThreadInfo) で
キャレット（テキストカーソル）の有無を確認して行う。
"""

import time
import ctypes
import ctypes.wintypes
import threading

import keyboard
import pyperclip

from ui.popup import show_result_popup


class GUITHREADINFO(ctypes.Structure):
    """Win32 GUITHREADINFO構造体"""
    _fields_ = [
        ("cbSize", ctypes.wintypes.DWORD),
        ("flags", ctypes.wintypes.DWORD),
        ("hwndActive", ctypes.wintypes.HWND),
        ("hwndFocus", ctypes.wintypes.HWND),
        ("hwndCapture", ctypes.wintypes.HWND),
        ("hwndMenuOwner", ctypes.wintypes.HWND),
        ("hwndMoveSize", ctypes.wintypes.HWND),
        ("hwndCaret", ctypes.wintypes.HWND),
        ("rcCaret", ctypes.wintypes.RECT),
    ]


class OutputManager:
    """テキスト出力管理クラス"""

    def output_text(self, text: str) -> None:
        """整形済みテキストを出力する

        - テキストボックスにカーソルがある場合: Ctrl+Vで直接貼り付け
        - テキストボックスがない場合: ポップアップでコピーボタンを表示
        """
        if self._has_active_text_input():
            # テキストボックスがアクティブ → 直接貼り付け
            pyperclip.copy(text)
            time.sleep(0.05)
            keyboard.send("ctrl+v")
        else:
            # テキストボックスがない → ポップアップ表示
            self._show_popup_async(text)

    def _has_active_text_input(self) -> bool:
        """テキスト入力可能なフィールドにカーソルがあるかを判定する

        Win32 API の GetGUIThreadInfo でキャレット（テキストカーソル）の
        存在するウィンドウハンドルを取得。0でなければテキスト入力中。
        """
        try:
            user32 = ctypes.windll.user32
            gui_info = GUITHREADINFO()
            gui_info.cbSize = ctypes.sizeof(GUITHREADINFO)

            # フォアグラウンドウィンドウのスレッドIDを取得
            hwnd = user32.GetForegroundWindow()
            thread_id = user32.GetWindowThreadProcessId(hwnd, None)

            if user32.GetGUIThreadInfo(thread_id, ctypes.byref(gui_info)):
                # hwndCaret: キャレットが存在するウィンドウハンドル
                # 0でなければテキスト入力フィールドがアクティブ
                return gui_info.hwndCaret != 0

            return False
        except Exception:
            # 判定に失敗した場合は安全側（ポップアップを出す）
            return False

    def _show_popup_async(self, text: str) -> None:
        """ポップアップを別スレッドで表示する（メインスレッドをブロックしない）"""
        threading.Thread(
            target=show_result_popup,
            args=(text,),
            daemon=True,
        ).start()
