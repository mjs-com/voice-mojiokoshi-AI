"""音声キャプチャモジュール

マイクから音声を録音し、WAV形式のバイトデータとして提供する。
sounddeviceライブラリを使用してリアルタイムに音声を取得する。
"""

import io
import wave
import threading
import numpy as np
import sounddevice as sd


class AudioCapture:
    """マイク音声のキャプチャ・バッファリングを行うクラス"""

    def __init__(self, sample_rate: int = 16000, channels: int = 1):
        self.sample_rate = sample_rate
        self.channels = channels
        self.is_recording = False
        self._frames: list[np.ndarray] = []
        self._stream: sd.InputStream | None = None
        self._lock = threading.Lock()

    def start(self) -> None:
        """録音を開始する"""
        with self._lock:
            self._frames = []
            self.is_recording = True
            self._stream = sd.InputStream(
                samplerate=self.sample_rate,
                channels=self.channels,
                dtype="int16",
                blocksize=1024,
                callback=self._audio_callback,
            )
            self._stream.start()

    def stop(self) -> None:
        """録音を停止する"""
        with self._lock:
            self.is_recording = False
            if self._stream is not None:
                self._stream.stop()
                self._stream.close()
                self._stream = None

    def _audio_callback(self, indata: np.ndarray, frames: int, time_info, status) -> None:
        """sounddeviceのコールバック（オーディオスレッドで実行される）"""
        if self.is_recording:
            # CPythonのGILにより list.append() はスレッドセーフ
            self._frames.append(indata.copy())

    def get_audio_data(self) -> io.BytesIO | None:
        """録音済み音声をWAV形式のBytesIOとして取得する（全体）"""
        if not self._frames:
            return None
        return self._to_wav(self._frames)

    def get_partial_audio(self) -> io.BytesIO | None:
        """現在までの録音済み音声をWAV形式のBytesIOとして取得する（リアルタイムSTT用）"""
        if not self._frames:
            return None
        # フレームのスナップショットを取得（録音中も安全）
        frames_snapshot = list(self._frames)
        return self._to_wav(frames_snapshot)

    def _to_wav(self, frames: list[np.ndarray]) -> io.BytesIO:
        """numpy配列のリストをWAV形式のBytesIOに変換する"""
        audio = np.concatenate(frames).flatten()
        buf = io.BytesIO()
        with wave.open(buf, "wb") as wf:
            wf.setnchannels(self.channels)
            wf.setsampwidth(2)  # 16bit = 2bytes
            wf.setframerate(self.sample_rate)
            wf.writeframes(audio.tobytes())
        buf.seek(0)
        return buf

    def get_duration(self) -> float:
        """現在の録音時間（秒）を返す"""
        if not self._frames:
            return 0.0
        total_samples = sum(f.shape[0] for f in self._frames)
        return total_samples / self.sample_rate
