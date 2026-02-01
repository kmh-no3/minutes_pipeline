# B-0001.wav を対象にしたツールテスト手順

WAVE フォルダ内の **B-0001.wav** を入力として minutes-pipeline（mpipe）のテストを実行する手順です。  
**仮想環境を利用する想定**です。他プロジェクトとのバージョン競合を避けるため、必ず venv 内で実行してください。

## 前提

- プロジェクトルート: `minutes-pipeline/`
- 対象ファイル: `tests/data/input/SPREDS-D1.ver1.3.ja/ver1.3/ja/mixed/WAVE/B-0001.wav`
- **テスト用設定**（出力は `tests/output/` に納め、examples フォルダは鋳型のため使用しない）:
  - **開発環境（GPU あり）**: `tests/minutes_dev.yml` を使用（処理が速い）
  - **社用 PC など GPU なし**: `tests/minutes_large.yml` を使用
- **実行場所**: 以下の手順はすべて **WSL の bash** で行います（PowerShell / cmd では仮想環境の有効化コマンドが異なります）。

---

## 手順

### 1. プロジェクトルートに移動

```bash
cd /home/user/projects/minutes-pipeline
```

### 2. 仮想環境の作成（初回のみ）

```bash
python3 -m venv .venv
```

- 既に `.venv` がある場合はこのステップは不要です。
- `python3` が無い場合は `python -m venv .venv` を試してください。

### 3. 仮想環境の有効化

```bash
source .venv/bin/activate
```

成功すると、プロンプトの先頭に `(.venv)` が付きます。

**有効化できない場合の確認：**

| 確認項目 | 対処 |
|----------|------|
| シェルが WSL の bash か | Cursor のターミナルで「WSL: Ubuntu」などを選択し、bash で開き直す。 |
| `.venv` が存在するか | `ls -la .venv/bin/activate` でファイルがあるか確認。無ければ手順 2 を実行。 |
| パスにスペース・日本語が含まれていないか | プロジェクトをスペースや日本語の無いパス（例: `/home/user/projects/minutes-pipeline`）に置く。 |
| `source` が使えない | `. .venv/bin/activate` とドット＋スペースで試す。 |

**有効化せずに venv の Python だけ使う方法（代替）：**  
同じターミナルで、プロジェクトルートにいるときに  
`./.venv/bin/python -m minutes_pipeline.cli run ...` のように、`.venv` 内の `python` を直接指定すれば、有効化なしでもバージョンは venv に閉じたまま実行できます。

### 4. パッケージのインストール（初回のみ、有効化したあと）

```bash
pip install -U pip
pip install -e ".[jsonschema]"
```

- **音声認識（ASR）を使う場合**は、次のいずれかを実行してください（未インストールだと `mpipe run` で Whisper エラーになります）。
  ```bash
  pip install openai-whisper
  ```
  またはオプション指定で一括:
  ```bash
  pip install -e ".[jsonschema,asr]"
  ```

### 5. B-0001.wav でパイプラインを実行

有効化した仮想環境のまま、**開発用設定**（GPU で速い）を使って実行します。出力は **tests 内**（`tests/output/`）に納まります。

```bash
mpipe run tests/data/input/SPREDS-D1.ver1.3.ja/ver1.3/ja/mixed/WAVE/B-0001.wav \
  --config tests/minutes_dev.yml
```

- 出力は **`tests/output/<日付>_B-0001/`** に生成されます（examples フォルダは鋳型のため使用せず、汚しません）。
- GPU がない環境では `--config tests/minutes_large.yml` を使ってください。

### 6. 出力の確認

以下ができているか確認します。

- `tests/output/<実行ID>/transcript_clean.json` … 前処理済み文字起こし
- `tests/output/<実行ID>/llm_instructions.md` … LLM 用指示（要約エンジンが manual の場合）
- `tests/output/<実行ID>/llm_transcript.txt` … LLM に渡す文字起こしテキスト

要約を API で行う設定にしている場合は、`minutes_draft.md` や `llm_output.json` なども出力されます。

### 7. 手動要約フローで試す場合（オプション）

`tests/minutes_dev.yml`（または `tests/minutes_large.yml`）の `summarize.engine` が `manual` のときは、リクエストパックを生成してから ChatGPT/Copilot で要約できます。**仮想環境は有効化したまま**にします。

```bash
# <実行ID> は実際のフォルダ名（例: 20250130_B-0001）に置き換え
mpipe request tests/output/<実行ID>/transcript_clean.json \
  --config tests/minutes_dev.yml
```

返ってきた JSON を `llm_output.json` として保存したあと：

```bash
mpipe apply tests/output/<実行ID>/llm_output.json \
  --transcript tests/output/<実行ID>/transcript_clean.json \
  --config tests/minutes_dev.yml
```

---

## パスの補足（Windows から見た場合）

- エクスプローラーなどでは:  
  `\\wsl.localhost\Ubuntu\home\user\projects\minutes-pipeline\tests\data\input\SPREDS-D1.ver1.3.ja\ver1.3\ja\mixed\WAVE\B-0001.wav`
- コマンドは **WSL の bash 内**で実行するため、手順ではスラッシュのパス（`tests/data/input/...`）を使います。

## トラブルシュート

- **Whisper 未インストール**: エラー「Whisper backend not found」が出た場合は、仮想環境内で `pip install openai-whisper` または `pip install -e ".[asr]"` を実行してください。
- **開発用設定（minutes_dev.yml）は GPU 必須**: GPU がない環境では `tests/minutes_large.yml` を使ってください。
- **メモリ不足**: `minutes_large.yml` の `asr.model` を `base` や `small` に下げると軽くなります。
- **設定のパス**: `tests/minutes_dev.yml` および `tests/minutes_large.yml` 内の `prompt_path` / `schema_path` 等は、設定ファイルの親ディレクトリ（`tests/`）基準の相対パスです。テスト用設定では examples を `../examples/project-template/...` で参照しており、examples フォルダ自体は書き込みされません。
