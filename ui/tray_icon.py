"""システムトレイアイコンモジュール

タスクバー右下にアイコンを常駐させ、
右クリックメニューから設定・終了などを操作する。

※ Windowsでは新しいアプリのトレイアイコンは
   「隠れたインジケーター」（△マーク）の中に入ることがあります。
   タスクバー右下の「^」ボタンを押すと表示されます。
"""

import threading
from PIL import Image, ImageDraw, ImageFont
import pystray


class TrayIcon:
    """システムトレイアイコン管理クラス"""

    def __init__(self, app):
        self._app = app
        self._icon: pystray.Icon | None = None
        self._is_recording = False

    def start(self) -> None:
        """システムトレイアイコンを表示する（別スレッドで実行）"""
        icon = pystray.Icon(
            name="指いらず",
            icon=self._create_icon(recording=False),
            title="指いらず - 待機中",
            menu=self._build_menu(),
        )
        self._icon = icon
        # pystray.run() はメインスレッドでないと動作しないケースがあるが
        # daemon=True のスレッドで動かすことで終了時に自動で止まる
        thread = threading.Thread(target=icon.run, daemon=True)
        thread.start()

    def stop(self) -> None:
        if self._icon:
            try:
                self._icon.stop()
            except Exception:
                pass

    def set_recording(self, is_recording: bool) -> None:
        self._is_recording = is_recording
        if self._icon:
            try:
                self._icon.icon = self._create_icon(recording=is_recording)
                self._icon.title = (
                    "指いらず - 録音中..." if is_recording
                    else "指いらず - 待機中"
                )
            except Exception:
                pass

    def set_processing(self) -> None:
        if self._icon:
            try:
                self._icon.title = "指いらず - AI整形中..."
            except Exception:
                pass

    def _build_menu(self) -> pystray.Menu:
        return pystray.Menu(
            pystray.MenuItem("指いらず v0.2", None, enabled=False),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("設定", self._on_settings),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("終了", self._on_quit),
        )

    def _on_settings(self, icon, item) -> None:
        threading.Thread(target=self._app.open_settings, daemon=True).start()

    def _on_quit(self, icon, item) -> None:
        self._app.quit()

    @staticmethod
    def _create_icon(recording: bool = False) -> Image.Image:
        """トレイアイコン画像を生成する（ICO互換の正方形画像）

        Windows のシステムトレイは 16x16 が基本だが、
        高DPI環境では大きい画像を縮小して使う。
        """
        size = 64
        img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        if recording:
            # 録音中: 赤い丸に白い■（停止マーク）
            draw.ellipse([2, 2, size - 2, size - 2], fill=(220, 50, 50, 255))
            sq = 18
            cx, cy = size // 2, size // 2
            draw.rectangle(
                [cx - sq // 2, cy - sq // 2, cx + sq // 2, cy + sq // 2],
                fill=(255, 255, 255, 255),
            )
        else:
            # 待機中: 青い丸に白い「Y」（指いらずの頭文字風）
            draw.ellipse([2, 2, size - 2, size - 2], fill=(74, 158, 255, 255))
            # マイクっぽいシンプルな形
            cx, cy = size // 2, size // 2
            # マイクの頭（楕円）
            draw.ellipse([cx - 8, cy - 18, cx + 8, cy + 2], fill=(255, 255, 255, 255))
            # マイクの棒
            draw.rectangle([cx - 3, cy + 2, cx + 3, cy + 14], fill=(255, 255, 255, 255))
            # マイクの台座
            draw.rectangle([cx - 10, cy + 14, cx + 10, cy + 18], fill=(255, 255, 255, 255))

        return img
