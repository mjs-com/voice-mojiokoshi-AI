"""Google Free STT エンジン

speech_recognition ライブラリ経由で Google の無料音声認識 API を使用する。
APIキー不要・無料で利用可能。日本語の認識精度はまずまず。
インターネット接続が必要。

※ Phase 1 のデフォルトSTTエンジン。
※ 精度に不満がある場合は、Phase 3 で Faster Whisper 等に差し替え可能。
"""

import io

import speech_recognition as sr

from .base import STTEngine


class GoogleFreeSTT(STTEngine):
    """Google 無料音声認識APIを使用するSTTエンジン"""

    def __init__(self, language: str = "ja-JP"):
        self._recognizer = sr.Recognizer()
        self._language = language

    def transcribe(self, audio_data: io.BytesIO) -> str:
        """WAV形式の音声データをテキストに変換する"""
        try:
            audio_data.seek(0)
            with sr.AudioFile(audio_data) as source:
                audio = self._recognizer.record(source)

            text = self._recognizer.recognize_google(
                audio, language=self._language
            )
            return text

        except sr.UnknownValueError:
            # 音声を認識できなかった
            return ""
        except sr.RequestError as e:
            print(f"   STT通信エラー: {e}")
            return ""
        except Exception as e:
            print(f"   STTエラー: {e}")
            return ""

    def get_name(self) -> str:
        return "Google Free STT"
