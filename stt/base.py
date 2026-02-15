"""STT（音声認識）エンジンの基底クラス

すべてのSTTエンジンはこのインターフェースを実装する。
モジュール設計により、差し替えが可能。
"""

import io
from abc import ABC, abstractmethod


class STTEngine(ABC):
    """STTエンジンの抽象基底クラス"""

    @abstractmethod
    def transcribe(self, audio_data: io.BytesIO) -> str:
        """WAV形式の音声データをテキストに変換する

        Args:
            audio_data: WAV形式のBytesIOオブジェクト

        Returns:
            文字起こし結果のテキスト。認識できなかった場合は空文字列。
        """
        pass

    @abstractmethod
    def get_name(self) -> str:
        """エンジン名を返す"""
        pass
