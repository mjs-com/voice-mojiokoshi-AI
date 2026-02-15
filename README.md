# 指いらず（YubiIrazu）

AI音声文字起こし・整形アプリ。話した内容をリアルタイムで文字起こしし、AIで整形してカーソル位置に貼り付けます。

---

## 起動方法（コピペでOK）

### 方法1: ターミナルから起動

**PowerShell または コマンドプロンプト** を開き、プロジェクトフォルダに移動してから実行：

```powershell
cd "$env:USERPROFILE\OneDrive\ドキュメント\GitHub\voice-mojiokoshi-AI"
python main.py
```

※ フォルダ名が違う場合は、実際のパスに書き換えてください。

---

### 方法2: バッチファイルで起動（いちばん簡単）

1. エクスプローラーで **`voice-mojiokoshi-AI`** フォルダを開く
2. **`起動.bat`** をダブルクリック

これでコンソールが開き、指いらずが起動します。終了するときはコンソールで **Ctrl+C** を押すか、ウィンドウを閉じてください。

---

### 方法3: 1行で起動（フォルダを開いた状態で）

すでに **voice-mojiokoshi-AI** フォルダを開いている場合、PowerShellで次をコピペ：

```powershell
python main.py
```

---

## 初回だけ

- 依存パッケージが入っていない場合は、先に以下を実行：

```powershell
cd "$env:USERPROFILE\OneDrive\ドキュメント\GitHub\voice-mojiokoshi-AI"
python -m pip install -r requirements.txt
```

- APIキー未設定のときは、起動時にコンソールで入力するよう促されます。入力したキーは Windows 資格情報マネージャーに保存されます。

---

## 操作

| 操作 | キー（デフォルト） |
|------|---------------------|
| プッシュトゥトーク（長押しで録音） | **右Alt** 長押し |
| ハンズフリー（押すたびに開始/停止） | **F2** |
| 終了 | **Ctrl+C**（コンソールで） |
