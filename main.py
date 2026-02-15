"""指いらず - AI音声文字起こし・整形アプリ

Phase 2: UI・常駐化
- システムトレイ常駐（タスクバー右下にアイコン）
- 録音中インジケーター（画面右上にフローティング表示）
- リアルタイムプレビュー（録音中に生テキストを表示）
- 設定画面（ショートカット・LLM・プロンプト・自動起動）
- PC起動時の自動起動
"""

import sys
import os
import time
import threading

# プロジェクトルートをパスに追加
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.audio_capture import AudioCapture
from core.input_manager import InputManager
from core.output_manager import OutputManager
from core.system_manager import enable_auto_start, disable_auto_start
from stt.google_free_stt import GoogleFreeSTT
from llm.gemini_formatter import GeminiFormatter
from utils.settings import Settings
from utils.credential_manager import get_api_key, has_api_key, prompt_api_key
from ui.tray_icon import TrayIcon
from ui.indicator import RecordingIndicator
from ui.settings_window import SettingsWindow


class YubiIrazu:
    """指いらず メインアプリケーションクラス"""

    def __init__(self):
        self._print_banner()

        # 設定読み込み
        self.settings = Settings()

        # 音声キャプチャ
        self.audio = AudioCapture()

        # STTエンジン
        self.stt = GoogleFreeSTT()
        print(f"  STTエンジン: {self.stt.get_name()}")

        # LLMエンジン
        self.llm = self._init_llm()

        # 出力マネージャー
        self.output = OutputManager()

        # 入力マネージャー（ホットキー管理）
        self.input_manager = InputManager(
            settings=self.settings.config,
            on_recording_start=self._on_recording_start,
            on_recording_stop=self._on_recording_stop,
        )

        # UI
        self.tray = TrayIcon(self)
        self.indicator = RecordingIndicator()

        # リアルタイムSTT用
        self._partial_text = ""
        self._is_processing = False

        # 自動起動設定の反映
        self._apply_auto_start()

    def _print_banner(self) -> None:
        """起動バナーを表示"""
        print()
        print("=" * 50)
        print("  指いらず v0.2 (Phase 2)")
        print("  AI音声文字起こし・整形アプリ")
        print("=" * 50)
        print()

    def _init_llm(self) -> GeminiFormatter | None:
        """LLMエンジンを初期化する

        APIキーはWindows Credential Manager（資格情報マネージャー）から取得する。
        未登録の場合はコンソールで入力を求める。
        """
        llm_config = self.settings.get("llm", {})
        provider = llm_config.get("provider", "gemini")

        # Credential ManagerからAPIキーを取得
        api_key = get_api_key(provider)

        # 未登録の場合、初回セットアップとして入力を求める
        if not api_key:
            print()
            print("  ⚠️  APIキーが未登録です。")
            api_key = prompt_api_key(provider)

        if not api_key:
            print()
            print("     ※ APIキーなしでも録音・文字起こし（STT）はテスト可能です。")
            print("       LLM整形はスキップされ、生テキストがそのまま出力されます。")
            print()
            return None

        model = llm_config.get("model", "gemini-2.0-flash-lite")
        llm = GeminiFormatter(api_key=api_key, model=model)
        print(f"  LLMエンジン: {llm.get_name()}")
        print(f"  APIキー: Windows資格情報マネージャーに安全に保存済み")
        return llm

    def _apply_auto_start(self) -> None:
        """設定に基づいて自動起動を有効/無効にする"""
        if self.settings.get("auto_start", False):
            enable_auto_start()
        else:
            disable_auto_start()

    # ─── 録音コールバック ───

    def _on_recording_start(self) -> None:
        """録音開始コールバック（キーボードフックスレッドから呼ばれる）"""
        print("\n🎙  録音中... ", end="", flush=True)
        self.audio.start()
        self._partial_text = ""

        # UIの更新
        self.tray.set_recording(True)
        self.indicator.show()

        self._start_realtime_stt()

    def _on_recording_stop(self) -> None:
        """録音停止コールバック（キーボードフックスレッドから呼ばれる）"""
        self.audio.stop()
        self._stop_realtime_stt()
        duration = self.audio.get_duration()
        print(f"\n⏹  録音停止（{duration:.1f}秒）")

        # UI更新
        self.tray.set_recording(False)
        self.indicator.update_status("✨ AI整形中...")
        self.tray.set_processing()

        # 二重処理防止
        if self._is_processing:
            return
        self._is_processing = True

        # バックグラウンドで処理（キーボードフックスレッドをブロックしない）
        threading.Thread(target=self._process_recording, daemon=True).start()

    # ─── 録音処理パイプライン ───

    def _process_recording(self) -> None:
        """録音データの処理: STT → LLM → 出力"""
        try:
            # 最低録音時間チェック
            if self.audio.get_duration() < 0.3:
                print("   録音が短すぎます（0.3秒以上話してください）")
                return

            # 音声データ取得
            audio_data = self.audio.get_audio_data()
            if audio_data is None:
                print("   音声が検出されませんでした。")
                return

            # --- Stage 1: STT（文字起こし）---
            print("📝 文字起こし中...")
            raw_text = self.stt.transcribe(audio_data)
            if not raw_text:
                print("   文字起こしできませんでした。")
                return
            print(f"   生テキスト: {raw_text}")

            # --- Stage 2: LLM整形 ---
            if self.llm:
                print("✨ AI整形中...")
                self.indicator.update_status("✨ AI整形中...")
                prompt = self.settings.get("prompt", "{raw_text}")
                formatted_text = self.llm.format_text(raw_text, prompt)
                print(f"   整形済み: {formatted_text}")
            else:
                formatted_text = raw_text
                print("   ⚠️ LLM未設定 → 生テキストをそのまま使用")

            # --- Stage 3: 出力 ---
            self.indicator.hide()
            time.sleep(0.1)  # インジケーターが閉じるのを待つ
            self.output.output_text(formatted_text)
            print("📋 出力完了")

        except Exception as e:
            print(f"❌ 処理エラー: {e}")

        finally:
            self._is_processing = False
            self.indicator.hide()
            self.tray.set_recording(False)
            print("\n待機中...\n")

    # ─── リアルタイムSTT ───

    def _start_realtime_stt(self) -> None:
        """リアルタイムSTTを開始（3秒ごとに中間結果を表示）"""

        def periodic_stt():
            while self.audio.is_recording:
                time.sleep(3)
                if not self.audio.is_recording:
                    break

                audio_data = self.audio.get_partial_audio()
                if audio_data is None:
                    continue

                try:
                    text = self.stt.transcribe(audio_data)
                    if text and text != self._partial_text:
                        self._partial_text = text
                        print(f"\r   [プレビュー] {text}", end="", flush=True)
                        self.indicator.update_text(text)
                except Exception:
                    pass

        threading.Thread(target=periodic_stt, daemon=True).start()

    def _stop_realtime_stt(self) -> None:
        """リアルタイムSTTを停止（スレッドは自然に終了する）"""
        pass

    # ─── 設定画面・終了 ───

    def open_settings(self) -> None:
        """設定画面を開く"""
        settings_window = SettingsWindow(
            settings=self.settings,
            on_save_callback=self._on_settings_saved,
        )
        settings_window.show()

    def _on_settings_saved(self) -> None:
        """設定が保存されたときのコールバック"""
        print("  ⚙️  設定が保存されました。変更を反映するにはアプリを再起動してください。")
        self._apply_auto_start()

    def quit(self) -> None:
        """アプリケーションを終了する"""
        print("\n指いらず を終了します...")
        self.input_manager.stop()
        self.tray.stop()
        self.indicator.hide()
        print("終了しました。")
        os._exit(0)

    # ─── アプリ起動 ───

    def run(self) -> None:
        """アプリケーションのメインループを開始する"""
        hotkeys = self.settings.get("hotkeys", {})
        ptt_key = hotkeys.get("push_to_talk", "right alt")
        hf_key = hotkeys.get("hands_free", "f2")

        print(f"\n📌 操作方法:")
        print(f"   プッシュトゥトーク: [{ptt_key}] 長押し")
        print(f"   ハンズフリー:       [{hf_key}] トグル")
        print(f"   設定画面:           システムトレイアイコン右クリック → 設定")
        print(f"   終了:               システムトレイアイコン右クリック → 終了")
        print(f"                       またはコンソールで [Ctrl+C]")
        print()
        print("待機中... システムトレイにアイコンが表示されています。\n")

        # システムトレイアイコン起動
        self.tray.start()

        # ホットキー登録
        self.input_manager.start()

        try:
            while True:
                time.sleep(0.5)
        except KeyboardInterrupt:
            self.quit()


if __name__ == "__main__":
    app = YubiIrazu()
    app.run()
