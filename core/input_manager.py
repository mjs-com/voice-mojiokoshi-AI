"""ホットキー管理モジュール

キーボードのグローバルフックを使用して、ショートカットキーの
検知・占拠（suppress）を行い、録音開始/停止を制御する。

- プッシュトゥトーク: キー長押しで録音、離すと停止
- ハンズフリー: キー1回押しでトグル（開始/停止）
"""

import time
from enum import Enum
from typing import Callable

import keyboard


class RecordingState(Enum):
    """録音状態"""
    IDLE = "idle"
    RECORDING_PTT = "recording_ptt"      # プッシュトゥトーク録音中
    RECORDING_HF = "recording_hf"        # ハンズフリー録音中


class InputManager:
    """ホットキー管理・モード制御クラス

    Low-Level Keyboard Hook + suppress によって、
    登録キーを他アプリより最優先で占拠する。
    """

    def __init__(
        self,
        settings: dict,
        on_recording_start: Callable[[], None],
        on_recording_stop: Callable[[], None],
    ):
        self._settings = settings
        self._on_recording_start = on_recording_start
        self._on_recording_stop = on_recording_stop
        self._state = RecordingState.IDLE
        self._suppress = settings.get("suppress_hotkeys", True)
        self._last_hf_time: float = 0.0
        self._hooks: list = []

    def start(self) -> None:
        """ホットキーの登録を開始する"""
        hotkeys = self._settings.get("hotkeys", {})
        ptt_key = hotkeys.get("push_to_talk", "right alt")
        hf_key = hotkeys.get("hands_free", "f2")

        # プッシュトゥトーク: press/release 両方をフック
        hook_ptt = keyboard.hook_key(
            ptt_key, self._on_ptt_event, suppress=self._suppress
        )
        self._hooks.append(hook_ptt)

        # ハンズフリー: 同じキーでなければフック
        if hf_key.lower() != ptt_key.lower():
            hook_hf = keyboard.hook_key(
                hf_key, self._on_hf_event, suppress=self._suppress
            )
            self._hooks.append(hook_hf)

    def stop(self) -> None:
        """すべてのホットキーフックを解除する"""
        keyboard.unhook_all()
        self._hooks.clear()

    @property
    def is_recording(self) -> bool:
        return self._state != RecordingState.IDLE

    def _on_ptt_event(self, event: keyboard.KeyboardEvent) -> None:
        """プッシュトゥトーク: キーダウンで録音開始、キーアップで録音停止"""
        if event.event_type == "down":
            # 既にPTT録音中ならスキップ（キーリピート対策）
            if self._state == RecordingState.IDLE:
                self._state = RecordingState.RECORDING_PTT
                self._on_recording_start()

        elif event.event_type == "up":
            if self._state == RecordingState.RECORDING_PTT:
                self._state = RecordingState.IDLE
                self._on_recording_stop()

    def _on_hf_event(self, event: keyboard.KeyboardEvent) -> None:
        """ハンズフリー: キーダウンでトグル（開始/停止）"""
        if event.event_type != "down":
            return

        # デバウンス（300ms以内の連打を無視）
        now = time.time()
        if now - self._last_hf_time < 0.3:
            return
        self._last_hf_time = now

        if self._state == RecordingState.IDLE:
            self._state = RecordingState.RECORDING_HF
            self._on_recording_start()
        elif self._state == RecordingState.RECORDING_HF:
            self._state = RecordingState.IDLE
            self._on_recording_stop()
