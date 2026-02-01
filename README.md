# minutes-pipeline

Teams 録画（mp4）やその他メディア向けの **議事録パイプライン** を再利用可能な形で提供します：
`mp4/wav → ASR（Whisper）→ 前処理 → 要約 → Markdown`。

- リポジトリ名: **minutes-pipeline**
- Python パッケージ: **minutes_pipeline**
- CLI コマンド: **mpipe**

## 社内・制限環境でも使いやすい理由
業務PCで **API や高性能GPUが使えない** 場合でも、このパイプラインは利用できます：
- `ASR + 前処理` をローカルで実行（クラウド不要）。
- `mpipe request` で **LLM 用リクエストパック**（プロンプト＋文字起こしチャンク）を生成。
- **ChatGPT / Copilot のチャットUI** で要約（文字起こしファイルをアップロード）。
- 返ってきた JSON をファイルに保存し、`mpipe apply` で適用して Markdown を出力。

要約ステップだけ「対話型LLM」に任せつつ、コードはそのまま再利用できます。

## クイックスタート（Cursor 向け）

### 1) インストール（開発モード）
```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -U pip
pip install -e ".[jsonschema]"
# 利用可能な場合のみ
# pip install -e ".[openai,anthropic,ollama,jsonschema]"
```

### 2) プロジェクトフォルダを作成（クライアント・案件ごと）
テンプレートをコピー：
```bash
cp -r examples/project-template ./my-minutes-project
cd my-minutes-project
```

mp4 を `input/` に置き、実行：
```bash
mpipe run input/meeting.mp4
```
出力は `output/<日付>_<ファイル名>/` に生成されます。

### 3) ChatGPT/Copilot のUIのみ利用する場合（API なし）
リクエストパックを生成：
```bash
mpipe request output/<実行ID>/transcript_clean.json
```
`llm_transcript.txt` を ChatGPT/Copilot にアップロードし、`llm_instructions.md` の内容を貼り付けてください。

返ってきた JSON をコードフェンスなしで `llm_output.json` として保存し、適用：
```bash
mpipe apply output/<実行ID>/llm_output.json --transcript output/<実行ID>/transcript_clean.json
```

## テストデータ（mp4）
回帰テストやゴールデンセット用の mp4 は **`tests/data/input/`** に格納してください。  
詳細は [tests/data/README.md](tests/data/README.md) を参照。

## セキュリティとプライバシー
このリポジトリは **コードは公開**・**データは非公開** を前提にしています：
- 実際の mp4／文字起こしは **コミットしない** でください。
- プロジェクトの `.gitignore` で `input/`、`output/`、`logs/` を除外してください。

## ライセンス
MIT（必要に応じて変更可）。
