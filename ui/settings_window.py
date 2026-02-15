"""設定画面モジュール

ショートカットキー割り当て、LLMプロバイダー/モデル選択、
APIキー管理、整形プロンプトの編集、自動起動設定を行う。
APIキーはWindows Credential Managerに保存される。
"""

import tkinter as tk
from tkinter import ttk, messagebox

from utils.credential_manager import get_api_key, save_api_key, delete_api_key
from utils.prompt_presets import get_preset_names, get_preset_body_by_name, get_preset_name_matching_body


class SettingsWindow:
    """設定画面"""

    # LLMプロバイダーとモデルの選択肢
    PROVIDERS = {
        "gemini": {
            "name": "Google Gemini",
            "models": [
                "gemini-2.0-flash-lite",
                "gemini-2.0-flash",
                "gemini-2.5-flash",
                "gemini-1.5-flash",
            ],
        },
    }

    def __init__(self, settings, on_save_callback=None):
        """
        Args:
            settings: Settingsインスタンス
            on_save_callback: 保存時に呼ばれるコールバック
        """
        self._settings = settings
        self._on_save = on_save_callback
        self._root: tk.Tk | None = None
        self._capturing_key: str | None = None  # キーキャプチャ中のフィールド名

    def show(self) -> None:
        """設定画面を表示する"""
        self._root = tk.Tk()
        self._root.title("指いらず - 設定")
        self._root.configure(bg="#2b2b2b")
        self._root.resizable(False, False)

        win_w, win_h = 540, 680
        screen_w = self._root.winfo_screenwidth()
        screen_h = self._root.winfo_screenheight()
        x = (screen_w - win_w) // 2
        y = (screen_h - win_h) // 2
        self._root.geometry(f"{win_w}x{win_h}+{x}+{y}")
        self._root.attributes("-topmost", True)

        config = self._settings.config

        # --- スタイル定義 ---
        label_style = {"bg": "#2b2b2b", "fg": "#e0e0e0", "font": ("メイリオ", 10)}
        header_style = {"bg": "#2b2b2b", "fg": "#4a9eff", "font": ("メイリオ", 11, "bold")}
        entry_style = {"bg": "#3c3c3c", "fg": "#e0e0e0", "insertbackground": "#e0e0e0",
                       "relief": tk.FLAT, "font": ("メイリオ", 10)}

        main_frame = tk.Frame(self._root, bg="#2b2b2b")
        main_frame.pack(fill=tk.BOTH, expand=True, padx=16, pady=12)

        # ─── ショートカットキー設定 ───
        tk.Label(main_frame, text="■ ショートカットキー", **header_style).pack(anchor="w", pady=(0, 6))

        hotkeys = config.get("hotkeys", {})

        # プッシュトゥトーク
        ptt_frame = tk.Frame(main_frame, bg="#2b2b2b")
        ptt_frame.pack(fill=tk.X, pady=2)
        tk.Label(ptt_frame, text="プッシュトゥトーク:", width=20, anchor="w", **label_style).pack(side=tk.LEFT)
        self._ptt_var = tk.StringVar(value=hotkeys.get("push_to_talk", "right alt"))
        self._ptt_entry = tk.Entry(ptt_frame, textvariable=self._ptt_var, width=18, state="readonly", **entry_style)
        self._ptt_entry.pack(side=tk.LEFT, padx=(0, 6))
        tk.Button(ptt_frame, text="変更", command=lambda: self._start_key_capture("ptt"),
                  bg="#555555", fg="white", relief=tk.FLAT, font=("メイリオ", 9)).pack(side=tk.LEFT)

        # ハンズフリー
        hf_frame = tk.Frame(main_frame, bg="#2b2b2b")
        hf_frame.pack(fill=tk.X, pady=2)
        tk.Label(hf_frame, text="ハンズフリー:", width=20, anchor="w", **label_style).pack(side=tk.LEFT)
        self._hf_var = tk.StringVar(value=hotkeys.get("hands_free", "f2"))
        self._hf_entry = tk.Entry(hf_frame, textvariable=self._hf_var, width=18, state="readonly", **entry_style)
        self._hf_entry.pack(side=tk.LEFT, padx=(0, 6))
        tk.Button(hf_frame, text="変更", command=lambda: self._start_key_capture("hf"),
                  bg="#555555", fg="white", relief=tk.FLAT, font=("メイリオ", 9)).pack(side=tk.LEFT)

        # キー占拠
        suppress_frame = tk.Frame(main_frame, bg="#2b2b2b")
        suppress_frame.pack(fill=tk.X, pady=2)
        tk.Label(suppress_frame, text="キー占拠:", width=20, anchor="w", **label_style).pack(side=tk.LEFT)
        self._suppress_var = tk.BooleanVar(value=config.get("suppress_hotkeys", True))
        tk.Checkbutton(suppress_frame, text="ON（他アプリのキー機能を無効化）",
                       variable=self._suppress_var, bg="#2b2b2b", fg="#e0e0e0",
                       selectcolor="#3c3c3c", activebackground="#2b2b2b",
                       font=("メイリオ", 9)).pack(side=tk.LEFT)

        # ─── 区切り ───
        tk.Frame(main_frame, height=1, bg="#444444").pack(fill=tk.X, pady=10)

        # ─── LLM設定 ───
        tk.Label(main_frame, text="■ AI整形（LLM）", **header_style).pack(anchor="w", pady=(0, 6))

        llm_config = config.get("llm", {})

        # モデル
        model_frame = tk.Frame(main_frame, bg="#2b2b2b")
        model_frame.pack(fill=tk.X, pady=2)
        tk.Label(model_frame, text="モデル:", width=20, anchor="w", **label_style).pack(side=tk.LEFT)
        models = self.PROVIDERS["gemini"]["models"]
        self._model_var = tk.StringVar(value=llm_config.get("model", "gemini-2.0-flash-lite"))
        model_combo = ttk.Combobox(model_frame, textvariable=self._model_var,
                                   values=models, state="readonly", width=24)
        model_combo.pack(side=tk.LEFT)

        # APIキー
        api_frame = tk.Frame(main_frame, bg="#2b2b2b")
        api_frame.pack(fill=tk.X, pady=2)
        tk.Label(api_frame, text="APIキー:", width=20, anchor="w", **label_style).pack(side=tk.LEFT)

        provider = llm_config.get("provider", "gemini")
        existing_key = get_api_key(provider) or ""
        masked = "●" * min(len(existing_key), 20) if existing_key else "(未設定)"
        self._api_display_var = tk.StringVar(value=masked)
        self._api_actual = existing_key
        self._api_entry = tk.Entry(api_frame, textvariable=self._api_display_var,
                                   width=24, show="", **entry_style)
        self._api_entry.pack(side=tk.LEFT, padx=(0, 6))

        tk.Button(api_frame, text="変更", command=self._change_api_key,
                  bg="#555555", fg="white", relief=tk.FLAT, font=("メイリオ", 9)).pack(side=tk.LEFT, padx=2)
        tk.Button(api_frame, text="削除", command=self._delete_api_key,
                  bg="#884444", fg="white", relief=tk.FLAT, font=("メイリオ", 9)).pack(side=tk.LEFT, padx=2)

        api_note = tk.Label(main_frame, text="※ APIキーはWindows資格情報マネージャーに安全に保存されます",
                            bg="#2b2b2b", fg="#888888", font=("メイリオ", 8))
        api_note.pack(anchor="w", padx=(0, 0), pady=(0, 4))

        # ─── 区切り ───
        tk.Frame(main_frame, height=1, bg="#444444").pack(fill=tk.X, pady=10)

        # ─── プロンプト設定 ───
        tk.Label(main_frame, text="■ 整形プロンプト", **header_style).pack(anchor="w", pady=(0, 6))

        # プリセット選択
        preset_frame = tk.Frame(main_frame, bg="#2b2b2b")
        preset_frame.pack(fill=tk.X, pady=(0, 4))
        tk.Label(preset_frame, text="プリセット:", width=12, anchor="w", **label_style).pack(side=tk.LEFT)
        preset_names = ["カスタム（現在の内容）"] + get_preset_names()
        self._preset_var = tk.StringVar(value="カスタム（現在の内容）")
        self._preset_combo = ttk.Combobox(
            preset_frame,
            textvariable=self._preset_var,
            values=preset_names,
            state="readonly",
            width=28,
        )
        self._preset_combo.pack(side=tk.LEFT, padx=(0, 6))
        tk.Button(
            preset_frame,
            text="このプリセットを適用",
            command=self._apply_preset,
            bg="#555555",
            fg="white",
            relief=tk.FLAT,
            font=("メイリオ", 9),
        ).pack(side=tk.LEFT)

        tk.Label(
            main_frame,
            text="※ 下の枠内でプロンプトを直接編集できます。編集後は「保存」を押してください。",
            bg="#2b2b2b",
            fg="#888888",
            font=("メイリオ", 8),
        ).pack(anchor="w", pady=(0, 2))

        self._prompt_text = tk.Text(
            main_frame, height=10, wrap=tk.WORD,
            bg="#3c3c3c", fg="#e0e0e0", insertbackground="#e0e0e0",
            relief=tk.FLAT, font=("メイリオ", 9), padx=6, pady=6,
        )
        current_prompt = config.get("prompt", "")
        self._prompt_text.insert("1.0", current_prompt)
        self._prompt_text.pack(fill=tk.X, pady=2)

        # 現在のプロンプトに一致するプリセットがあればコンボボックスに反映
        matching_name = get_preset_name_matching_body(current_prompt)
        if matching_name:
            self._preset_var.set(matching_name)
        else:
            self._preset_var.set("カスタム（現在の内容）")

        # ─── 区切り ───
        tk.Frame(main_frame, height=1, bg="#444444").pack(fill=tk.X, pady=10)

        # ─── 起動設定 ───
        tk.Label(main_frame, text="■ 起動設定", **header_style).pack(anchor="w", pady=(0, 6))
        self._auto_start_var = tk.BooleanVar(value=config.get("auto_start", False))
        tk.Checkbutton(main_frame, text="PC起動時に自動起動",
                       variable=self._auto_start_var, bg="#2b2b2b", fg="#e0e0e0",
                       selectcolor="#3c3c3c", activebackground="#2b2b2b",
                       font=("メイリオ", 10)).pack(anchor="w")

        # ─── 保存/キャンセルボタン ───
        btn_frame = tk.Frame(main_frame, bg="#2b2b2b")
        btn_frame.pack(pady=(16, 0))

        tk.Button(btn_frame, text="保存", command=self._save, width=14,
                  bg="#4a9eff", fg="white", activebackground="#3a8eef",
                  relief=tk.FLAT, font=("メイリオ", 10)).pack(side=tk.LEFT, padx=8)
        tk.Button(btn_frame, text="キャンセル", command=self._root.destroy, width=14,
                  bg="#555555", fg="white", activebackground="#666666",
                  relief=tk.FLAT, font=("メイリオ", 10)).pack(side=tk.LEFT, padx=8)

        self._root.mainloop()

    # ─── キーキャプチャ ───

    def _start_key_capture(self, field: str) -> None:
        """キー割り当てのキャプチャを開始する"""
        self._capturing_key = field
        var = self._ptt_var if field == "ptt" else self._hf_var
        var.set("キーを押してください...")

        # 全キー入力をキャプチャ
        self._root.bind("<Key>", self._on_key_captured)
        self._root.focus_set()

    def _apply_preset(self) -> None:
        """選択したプリセットをテキストエリアに適用する"""
        name = self._preset_var.get()
        if not name or name == "カスタム（現在の内容）":
            messagebox.showinfo("ヒント", "プリセットを選択してから「このプリセットを適用」を押してください。",
                                parent=self._root)
            return
        body = get_preset_body_by_name(name)
        if not body:
            messagebox.showwarning("エラー", f"プリセット「{name}」の内容を取得できませんでした。",
                                   parent=self._root)
            return
        self._prompt_text.delete("1.0", tk.END)
        self._prompt_text.insert("1.0", body)
        messagebox.showinfo("適用完了", "プリセットを反映しました。必要に応じて編集してから「保存」を押してください。",
                            parent=self._root)

    def _on_key_captured(self, event) -> None:
        """キーが押されたときのハンドラ"""
        if not self._capturing_key:
            return

        key_name = event.keysym.lower()
        # 特殊キーの名前を補正
        key_map = {
            "alt_r": "right alt", "alt_l": "left alt",
            "control_r": "right ctrl", "control_l": "left ctrl",
            "shift_r": "right shift", "shift_l": "left shift",
            "super_l": "left windows", "super_r": "right windows",
        }
        key_name = key_map.get(key_name, key_name)

        var = self._ptt_var if self._capturing_key == "ptt" else self._hf_var
        var.set(key_name)

        self._capturing_key = None
        self._root.unbind("<Key>")

    # ─── APIキー管理 ───

    def _change_api_key(self) -> None:
        """APIキー変更ダイアログ"""
        dialog = tk.Toplevel(self._root)
        dialog.title("APIキーの変更")
        dialog.configure(bg="#2b2b2b")
        dialog.geometry("400x130")
        dialog.attributes("-topmost", True)
        dialog.resizable(False, False)

        tk.Label(dialog, text="新しいAPIキーを入力:", bg="#2b2b2b", fg="#e0e0e0",
                 font=("メイリオ", 10)).pack(padx=12, pady=(12, 4), anchor="w")

        key_var = tk.StringVar()
        entry = tk.Entry(dialog, textvariable=key_var, width=50,
                         bg="#3c3c3c", fg="#e0e0e0", insertbackground="#e0e0e0",
                         relief=tk.FLAT, font=("メイリオ", 10))
        entry.pack(padx=12, pady=4)
        entry.focus_set()

        def save_key():
            new_key = key_var.get().strip()
            if new_key:
                provider = self._settings.config.get("llm", {}).get("provider", "gemini")
                save_api_key(provider, new_key)
                self._api_actual = new_key
                self._api_display_var.set("●" * min(len(new_key), 20))
                dialog.destroy()
                messagebox.showinfo("完了", "APIキーをWindows資格情報マネージャーに保存しました。",
                                    parent=self._root)

        tk.Button(dialog, text="保存", command=save_key,
                  bg="#4a9eff", fg="white", relief=tk.FLAT,
                  font=("メイリオ", 10), width=10).pack(pady=8)

    def _delete_api_key(self) -> None:
        """APIキーを削除する"""
        if messagebox.askyesno("確認", "APIキーを削除しますか？", parent=self._root):
            provider = self._settings.config.get("llm", {}).get("provider", "gemini")
            delete_api_key(provider)
            self._api_actual = ""
            self._api_display_var.set("(未設定)")

    # ─── 保存 ───

    def _save(self) -> None:
        """設定を保存してウィンドウを閉じる"""
        config = self._settings.config

        # ホットキー
        config["hotkeys"]["push_to_talk"] = self._ptt_var.get()
        config["hotkeys"]["hands_free"] = self._hf_var.get()
        config["suppress_hotkeys"] = self._suppress_var.get()

        # LLM
        config["llm"]["model"] = self._model_var.get()

        # プロンプト
        config["prompt"] = self._prompt_text.get("1.0", tk.END).strip()

        # 自動起動
        config["auto_start"] = self._auto_start_var.get()

        self._settings.save()

        if self._on_save:
            self._on_save()

        self._root.destroy()
