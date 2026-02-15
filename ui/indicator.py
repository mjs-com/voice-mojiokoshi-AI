"""録音中インジケーターモジュール

録音中に画面中央下にフローティングウィンドウを表示し、
録音状態とリアルタイムプレビューテキストを表示する。
ドラッグで好きな位置に移動可能。
"""

import tkinter as tk
import threading


class RecordingIndicator:
    """録音中インジケーターウィンドウ（ドラッグ移動対応）"""

    def __init__(self):
        self._root: tk.Tk | None = None
        self._text_label: tk.Label | None = None
        self._status_label: tk.Label | None = None
        self._is_visible = False
        self._lock = threading.Lock()
        # ドラッグ用
        self._drag_x = 0
        self._drag_y = 0

    def show(self) -> None:
        """インジケーターを表示する（別スレッドから呼ぶ）"""
        threading.Thread(target=self._create_window, daemon=True).start()

    def hide(self) -> None:
        """インジケーターを閉じる"""
        with self._lock:
            self._is_visible = False
            if self._root:
                try:
                    self._root.after(0, self._safe_destroy)
                except Exception:
                    pass

    def update_text(self, text: str) -> None:
        """プレビューテキストを更新する"""
        if self._root and self._text_label and self._is_visible:
            try:
                display = text[-200:] if len(text) > 200 else text
                self._root.after(0, lambda: self._safe_update_text(display))
            except Exception:
                pass

    def update_status(self, status: str) -> None:
        """ステータス表示を更新する"""
        if self._root and self._status_label and self._is_visible:
            try:
                self._root.after(0, lambda: self._safe_update_status(status))
            except Exception:
                pass

    def _create_window(self) -> None:
        """インジケーターウィンドウを作成する"""
        self._root = tk.Tk()
        self._root.title("")
        self._root.overrideredirect(True)  # タイトルバーなし
        self._root.attributes("-topmost", True)
        self._root.attributes("-alpha", 0.92)
        self._root.configure(bg="#1a1a2e")

        # 画面中央下に配置
        screen_w = self._root.winfo_screenwidth()
        screen_h = self._root.winfo_screenheight()
        win_w = 420
        win_h = 100
        x = (screen_w - win_w) // 2
        y = screen_h - win_h - 100
        self._root.geometry(f"{win_w}x{win_h}+{x}+{y}")

        # 角丸風の外枠
        outer = tk.Frame(self._root, bg="#1a1a2e", padx=2, pady=2)
        outer.pack(fill=tk.BOTH, expand=True)

        inner = tk.Frame(outer, bg="#16213e")
        inner.pack(fill=tk.BOTH, expand=True)

        # ステータスバー（上部）: ドラッグハンドル兼ステータス表示
        header = tk.Frame(inner, bg="#0f3460", cursor="fleur")
        header.pack(fill=tk.X)

        self._status_label = tk.Label(
            header,
            text="🎙 録音中...",
            font=("メイリオ", 11, "bold"),
            bg="#0f3460",
            fg="#e94560",
            anchor="w",
            padx=12,
            pady=6,
            cursor="fleur",
        )
        self._status_label.pack(fill=tk.X)

        # ドラッグイベントをヘッダーとステータスラベルの両方にバインド
        for widget in (header, self._status_label):
            widget.bind("<Button-1>", self._on_drag_start)
            widget.bind("<B1-Motion>", self._on_drag_motion)

        # プレビューテキスト
        self._text_label = tk.Label(
            inner,
            text="",
            font=("メイリオ", 10),
            bg="#16213e",
            fg="#e0e0e0",
            anchor="w",
            justify="left",
            wraplength=395,
            padx=12,
            pady=6,
        )
        self._text_label.pack(fill=tk.BOTH, expand=True)

        self._is_visible = True
        self._root.mainloop()

    # ─── ドラッグ移動 ───

    def _on_drag_start(self, event) -> None:
        """ドラッグ開始位置を記録する"""
        self._drag_x = event.x
        self._drag_y = event.y

    def _on_drag_motion(self, event) -> None:
        """ドラッグ中にウィンドウを移動する"""
        if self._root:
            x = self._root.winfo_x() + (event.x - self._drag_x)
            y = self._root.winfo_y() + (event.y - self._drag_y)
            self._root.geometry(f"+{x}+{y}")

    # ─── 安全なUI操作 ───

    def _safe_destroy(self) -> None:
        try:
            if self._root and self._root.winfo_exists():
                self._root.destroy()
        except tk.TclError:
            pass
        finally:
            self._root = None
            self._text_label = None
            self._status_label = None

    def _safe_update_text(self, text: str) -> None:
        try:
            if self._text_label and self._root and self._root.winfo_exists():
                self._text_label.config(text=text)
        except tk.TclError:
            pass

    def _safe_update_status(self, status: str) -> None:
        try:
            if self._status_label and self._root and self._root.winfo_exists():
                self._status_label.config(text=status)
        except tk.TclError:
            pass
