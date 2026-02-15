"""フォールバックポップアップモジュール

テキストボックスが選択されていない場合に、
整形済みテキストを表示するポップアップウィンドウ。
「コピー」ボタンでクリップボードにコピー可能。
"""

import tkinter as tk
import pyperclip


def show_result_popup(text: str, auto_close_ms: int = 15000) -> None:
    """整形済みテキストのポップアップを表示する

    Args:
        text: 表示するテキスト
        auto_close_ms: 自動で閉じるまでのミリ秒（デフォルト15秒）
    """
    try:
        root = tk.Tk()
        root.title("指いらず - 結果")
        root.attributes("-topmost", True)
        root.configure(bg="#2b2b2b")

        # 画面中央下に配置
        screen_w = root.winfo_screenwidth()
        screen_h = root.winfo_screenheight()
        win_w = 520
        win_h = 220
        x = (screen_w - win_w) // 2
        y = screen_h - win_h - 120
        root.geometry(f"{win_w}x{win_h}+{x}+{y}")
        root.resizable(False, False)

        # テキスト表示エリア
        text_frame = tk.Frame(root, bg="#2b2b2b")
        text_frame.pack(fill=tk.BOTH, expand=True, padx=12, pady=(12, 6))

        text_widget = tk.Text(
            text_frame,
            wrap=tk.WORD,
            height=7,
            font=("メイリオ", 11),
            bg="#3c3c3c",
            fg="#e0e0e0",
            insertbackground="#e0e0e0",
            relief=tk.FLAT,
            padx=8,
            pady=8,
        )
        text_widget.insert("1.0", text)
        text_widget.config(state="disabled")
        text_widget.pack(fill=tk.BOTH, expand=True)

        # ボタンエリア
        btn_frame = tk.Frame(root, bg="#2b2b2b")
        btn_frame.pack(pady=(4, 12))

        def copy_and_close():
            pyperclip.copy(text)
            root.destroy()

        btn_style = {
            "font": ("メイリオ", 10),
            "width": 12,
            "relief": tk.FLAT,
            "cursor": "hand2",
        }

        copy_btn = tk.Button(
            btn_frame,
            text="コピー",
            command=copy_and_close,
            bg="#4a9eff",
            fg="white",
            activebackground="#3a8eef",
            activeforeground="white",
            **btn_style,
        )
        copy_btn.pack(side=tk.LEFT, padx=6)

        close_btn = tk.Button(
            btn_frame,
            text="閉じる",
            command=root.destroy,
            bg="#555555",
            fg="white",
            activebackground="#666666",
            activeforeground="white",
            **btn_style,
        )
        close_btn.pack(side=tk.LEFT, padx=6)

        # 自動クローズ
        def safe_destroy():
            try:
                if root.winfo_exists():
                    root.destroy()
            except tk.TclError:
                pass

        root.after(auto_close_ms, safe_destroy)

        root.mainloop()

    except Exception as e:
        print(f"   ポップアップ表示エラー: {e}")
