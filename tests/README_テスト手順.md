# テスト手順

minutes-pipeline のテストを実行するための手順です。

## 前提

- Python 3.10 以上
- プロジェクトルート: `minutes-pipeline/`（この README の 1 階層上）

---

## 1. 環境準備

### 1.1 仮想環境の作成と有効化

```bash
# プロジェクトルートで
python -m venv .venv

# 有効化
# Linux / macOS (WSL 含む):
source .venv/bin/activate
# Windows (PowerShell):
# .venv\Scripts\Activate.ps1
```

### 1.2 パッケージのインストール

```bash
pip install -U pip
pip install -e ".[jsonschema]"
pip install pytest
```

---

## 2. ユニットテストの実行

```bash
# プロジェクトルートで
python -m pytest tests/ -v

# 特定のテストファイルのみ
python -m pytest tests/test_manual_pack.py -v
```

---

## 3. 既存テストデータで再実行（ChatGPT → apply）

文字起こし済みの既存フォルダ（例: `tests/output/2026-02-01_B-0002_gpu_lowvram`）を使い、**ChatGPT に JSON を生成してもらうところから** 議事録を再生成する手順です。

### 3.1 使うフォルダ

- **フォルダ**: `tests/output/2026-02-01_B-0002_gpu_lowvram`
- 既にあるファイル: `transcript_clean.json`, `llm_transcript.txt`, `llm_instructions.md`, `run_metadata.json` など

### 3.2 手順

#### Step A: 指示の更新（ToDo 一本化対応の指示を反映）

既存の `llm_instructions.md` は古い形式のままなので、現在のパイプラインで再生成します。プロジェクトルートで:

```bash
mpipe request tests/output/2026-02-01_B-0002_gpu_lowvram/transcript_clean.json
```

- `run_metadata.json` に `config_path` が入っているため、`--config` は不要です。
- 上記で `tests/output/2026-02-01_B-0002_gpu_lowvram/llm_instructions.md` と `llm_transcript.txt` が上書きされ、ToDo のみ・会議後のタスクのみの指示になります。

#### Step B: ChatGPT で JSON を生成

1. **ChatGPT（または Copilot）** を開く。
2. **llm_transcript.txt** を添付する。  
   - パス: `tests/output/2026-02-01_B-0002_gpu_lowvram/llm_transcript.txt`
3. **llm_instructions.md** の内容をすべてコピーし、チャットに貼り付けて送信する。
4. 返ってきた **JSON だけ** をコピーする（コードブロックの ``` や前後の説明文は含めない）。

#### Step C: JSON をファイルに保存

5. コピーした JSON を `tests/output/2026-02-01_B-0002_gpu_lowvram/llm_output.json` として保存する（既存ファイルを上書きしてよい）。
6. 先頭が `{`、末尾が `}` の 1 つの JSON オブジェクトになっていることを確認する。

#### Step D: apply で議事録 Markdown を生成

プロジェクトルートで:

```bash
mpipe apply tests/output/2026-02-01_B-0002_gpu_lowvram/llm_output.json --transcript tests/output/2026-02-01_B-0002_gpu_lowvram/transcript_clean.json
```

- 設定は `run_metadata.json` の `config_path` から自動で読まれるため、`--config` は不要です。
- 出力: `tests/output/2026-02-01_B-0002_gpu_lowvram/minutes_draft.md` が更新されます。

### 3.3 確認ポイント

生成された `minutes_draft.md` で次を確認してください。

- **「## 次のアクション」セクションがないこと**
- **「## ToDo」** に会議後のタスクのみが含まれていること
- 会議中のルール・手順（マイク/カメラオフ、質問はチャットへ等）が ToDo に含まれていないこと

### 3.4 設定を明示したい場合

別の `minutes.yml` を使う場合や、`run_metadata.json` がない場合は `--config` を指定します。

```bash
mpipe request tests/output/2026-02-01_B-0002_gpu_lowvram/transcript_clean.json --config tests/minutes_dev_lowvram.yml
# ... ChatGPT で JSON 取得 ...
mpipe apply tests/output/2026-02-01_B-0002_gpu_lowvram/llm_output.json --transcript tests/output/2026-02-01_B-0002_gpu_lowvram/transcript_clean.json --config tests/minutes_dev_lowvram.yml
```

---

## 4. 要約フォーマット確認（mock エンジン・任意）

議事録 Markdown が「ToDo のみ」で出ることを、LLM を使わずに確認する手順です。

```bash
cp -r examples/project-template ./test-run
cd test-run
```

`minutes.yml` の `summarize.engine` を `mock` にし:

```bash
mkdir -p output/sample
echo '{"language":"ja","segments":[{"start":0,"end":1,"speaker":"司会","text":"会議を始めます。"}]}' > output/sample/transcript_clean.json
mpipe summarize output/sample/transcript_clean.json --config minutes.yml
```

`output/sample/minutes_draft.md` に「次のアクション」がなく ToDo のみであることを確認します。

---

## 5. トラブルシューティング

| 現象 | 対処 |
|------|------|
| `ModuleNotFoundError: No module named 'minutes_pipeline'` | プロジェクトルートで `pip install -e .` を実行し、仮想環境が有効か確認する |
| `ModuleNotFoundError: No module named 'jsonschema'` | `pip install -e ".[jsonschema]"` を実行する |
| `pytest: command not found` | `pip install pytest` を実行する |
| `minutes.yml not found`（apply 時） | `run_metadata.json` と同じフォルダに config が無い場合は `--config tests/minutes_dev_lowvram.yml` を指定する |
| WSL でパスが通らない | `python -m pytest tests/ -v` のように `python -m pytest` で実行する |
