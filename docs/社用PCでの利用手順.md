# 社用PCで minutes-pipeline を使う手順

社用PCで本プロジェクトを利用する場合の手順です。ZIP でダウンロードし、WSL 上で展開・セットアップして実行します。

---

## 前提

- **Windows 社用PC** に **WSL（Windows Subsystem for Linux）** が入っていること
- Python 3.10 以上が WSL 内で利用できること（多くのディストリで `python3` で利用可能）
- 社用PCでは **GPU なし（CPU のみ）** を想定しています

---

## 1. プロジェクトを ZIP でダウンロード

1. 本リポジトリの **GitHub ページ** を開く
2. 緑色の **「Code」** ボタンをクリック
3. **「Download ZIP」** を選択し、ZIP ファイルを保存（例: `C:\Users\<あなた>\Downloads\minutes-pipeline-main.zip`）

※ リポジトリを clone できる環境の場合は `git clone` でも構いません。

---

## 2. WSL を起動し、ZIP を WSL 上に置いて展開

### 2.1 WSL のターミナルを開く

- Windows の「ターミナル」または「Ubuntu」など WSL 用アプリを起動

### 2.2 作業用ディレクトリを作成し、ZIP のパスを確認

Windows のダウンロードフォルダは WSL からは次のように参照できます。

```bash
# 作業用フォルダを作成（任意の場所でよい）
mkdir -p ~/projects
cd ~/projects
```

ZIP を WSL のホームから参照する例（ユーザ名は環境に合わせて読み替え）：

```bash
# Windows のダウンロードフォルダは通常次のようにアクセスできる
ls /mnt/c/Users/<Windowsのユーザ名>/Downloads/minutes-pipeline-*.zip
```

### 2.3 ZIP を展開

```bash
# 例: ダウンロードした ZIP を WSL の作業フォルダにコピーしてから展開
cp "/mnt/c/Users/<Windowsのユーザ名>/Downloads/minutes-pipeline-main.zip" ~/projects/
cd ~/projects
unzip minutes-pipeline-main.zip
cd minutes-pipeline-main
```

※ ZIP のファイル名は `minutes-pipeline-main.zip` や `minutes-pipeline-<ブランチ名>.zip` のようにリポジトリ名＋ブランチ名になっていることがあります。`unzip` で展開すると `minutes-pipeline-main` などのフォルダができるので、その中に `cd` してください。

展開後のディレクトリを「**プロジェクトルート**」と呼びます。

---

## 3. Python 仮想環境の作成とインストール

プロジェクトルートで以下を実行します。

### 3.1 Python のバージョン確認

```bash
python3 --version
# Python 3.10 以上であること
```

### 3.2 仮想環境の作成と有効化

```bash
cd ~/projects/minutes-pipeline-main   # プロジェクトルート
python3 -m venv .venv
source .venv/bin/activate
```

プロンプト先頭に `(.venv)` が出れば有効化できています。

### 3.3 パッケージのインストール

**ASR（音声認識）** と **JSON スキーマ** を使うための最小構成です。

```bash
pip install -U pip
pip install -e ".[asr,jsonschema]"
```

- `asr` … faster-whisper（推奨）または openai-whisper が入り、音声認識が使えます
- `jsonschema` … 設定・LLM 出力の検証に利用します

※ **faster-whisper** を優先して利用します。入っていない場合は openai-whisper にフォールバックし、処理が遅くなることがあります。

インストール確認：

```bash
mpipe --help
```

---

## 4. 自分の議事録用プロジェクトフォルダを作成

クライアント・案件ごとに 1 フォルダ作る想定です。

```bash
cd ~/projects/minutes-pipeline-main
cp -r examples/project-template ./my-minutes-project
cd my-minutes-project
```

- 音声・動画ファイルは **`input/`** に置きます
- テンプレートの `minutes.yml` は **CPU・large-v3・int8** のため、**GPU なしの社用PC** でそのまま使えます

---

## 5. 音声・動画を用意して実行

### 5.1 ファイルを input に置く

- 議事録にしたい **mp4** または **wav** を `my-minutes-project/input/` にコピーする  
  （例: `input/meeting_20250201.mp4`）

WSL から Windows のファイルをコピーする例：

```bash
cp "/mnt/c/Users/<ユーザ名>/Downloads/meeting_20250201.mp4" ~/projects/minutes-pipeline-main/my-minutes-project/input/
```

### 5.2 パイプラインを実行

```bash
cd ~/projects/minutes-pipeline-main/my-minutes-project
source ../.venv/bin/activate   # まだ有効でない場合
mpipe run input/meeting_20250201.mp4
```

- 出力は **`output/<日付>_<ファイル名>/`** に生成されます
- 社用PC（CPU のみ）では **25 分の音声でおおよそ 40 分〜2 時間** かかることがあります

---

## 6. 要約を ChatGPT / Copilot で行う場合（API なし）

ASR と前処理まで終わったあと、要約だけブラウザの ChatGPT や Copilot で行う手順です。

### 6.1 リクエストパックの生成

```bash
cd ~/projects/minutes-pipeline-main/my-minutes-project
mpipe request output/<実行ID>/transcript_clean.json
```

※ `<実行ID>` は `output/` 内のフォルダ名（例: `2026-02-01_meeting_20250201`）に置き換えます。

生成されるのは、そのフォルダ内の次のファイルです。

- `llm_transcript.txt` … 文字起こし（アップロード用）
- `llm_instructions.md` … プロンプト（コピペ用）

### 6.2 ChatGPT / Copilot で要約

1. **`llm_transcript.txt`** を ChatGPT または Copilot のチャットにアップロード
2. **`llm_instructions.md`** の内容をコピーしてチャットに貼り付け、要約を依頼
3. 返ってきた **JSON** を、コードブロック記号なしで **`llm_output.json`** として保存し、同じ `output/<実行ID>/` に置く

### 6.3 適用して Markdown を出力

```bash
mpipe apply output/<実行ID>/llm_output.json --transcript output/<実行ID>/transcript_clean.json
```

議事録の Markdown が、そのフォルダ内の `minutes_draft.md` などに出力されます。

---

## 7. 社用PCでの設定の目安（CPU のみ）

| 用途       | 設定ファイル／内容                         | 処理時間の目安（25分音声）   |
|------------|--------------------------------------------|------------------------------|
| そのまま使う | テンプレートの `minutes.yml`（CPU, large-v3） | 約 40 分〜2 時間             |
| 少し速くする | モデルを `base` や `small` に変更          | 短くなるが精度は落ちる       |

テンプレートの `minutes.yml` は既に `device: "cpu"` なので、**ZIP のまま社用PCで使う場合はそのままで問題ありません**。  
リポジトリ付属の `tests/minutes_large.yml` も CPU・large-v3 なので、設定の参考にできます。

---

## 8. トラブルシューティング

- **「No module named 'faster_whisper'」**  
  → `pip install -e ".[asr,jsonschema]"` を再度実行し、`faster-whisper` が入っているか確認してください。

- **処理が非常に遅い**  
  → [tests/ASR_SLOW_TROUBLESHOOTING.md](../tests/ASR_SLOW_TROUBLESHOOTING.md) を参照。faster-whisper が入っているか、メモリ不足でスワップが出ていないかを確認してください。

- **WSL で Python がない**  
  → `sudo apt update && sudo apt install -y python3 python3-venv python3-pip unzip` でインストールできます。

---

## 手順のまとめ（チェックリスト）

| # | 手順 |
|---|------|
| 1 | GitHub から「Download ZIP」でダウンロード |
| 2 | WSL を起動し、`~/projects` などに ZIP を置いて `unzip` で展開 |
| 3 | プロジェクトルートで `python3 -m venv .venv` → `source .venv/bin/activate` |
| 4 | `pip install -e ".[asr,jsonschema]"` でインストール |
| 5 | `cp -r examples/project-template ./my-minutes-project` で作業用フォルダ作成 |
| 6 | 音声・動画を `my-minutes-project/input/` に置き、`mpipe run input/<ファイル>` で実行 |
| 7 | （任意）`mpipe request` → ChatGPT/Copilot で要約 → `llm_output.json` を保存 → `mpipe apply` |

以上で、社用PCで ZIP を展開し、WSL 上で本プロジェクトを利用できます。
