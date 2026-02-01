# Cursor 引き継ぎ手順（minutes-pipeline）

## 1. このリポジトリをCursorで開く
- `minutes-pipeline/` をOpen Folder

## 2. 仮想環境 + インストール
```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -U pip
pip install -e ".[jsonschema]"
```

## 3. まず動作確認（テンプレプロジェクト）
```bash
cd examples/project-template
mpipe run input/meeting.mp4
```

## 4. APIや高性能PCが使えない場合（ChatGPT/Copilot UIだけで要約）
`examples/project-template/minutes.yml` の `summarize.engine` を `manual` にします（テンプレは既にmanual）。

実行後、出力フォルダに以下が出ます：
- `llm_instructions.md`（貼り付ける指示）
- `llm_transcript.txt`（ChatUIにアップロードする文字起こし）

手順：
1. ChatGPT/Copilotに `llm_transcript.txt` をアップロード
2. `llm_instructions.md` の指示を貼り付けて実行
3. 返ってきたJSONを `llm_output.json` として保存（コードフェンスなし）
4. 適用してmd生成：
```bash
mpipe apply output/<run>/llm_output.json --transcript output/<run>/transcript_clean.json
```

## 5. 余裕があれば
- `summarize.engine` を `openai/anthropic/ollama` に切り替え可能
