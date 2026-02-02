# GitHub へのプッシュ手順

リポジトリ https://github.com/kmh-no3/minutes_pipeline.git へ最新の変更をコミット・プッシュする手順です。

## 重要

**WSL のターミナル（bash）で実行してください。**  
Windows 側の Git から WSL 内のリポジトリを操作すると「dubious ownership」エラーになるため、プロジェクトは WSL 上（例: `~/projects/minutes-pipeline`）で `git` を実行する必要があります。

## 前提

- WSL のターミナルで、プロジェクトルート（`~/projects/minutes-pipeline` または `minutes-pipeline` を展開したディレクトリ）にいること
- GitHub の認証が済んでいること（HTTPS の場合は Personal Access Token、SSH の場合は鍵を設定）

---

## 方法 A: スクリプトで一括実行

プロジェクトルートで以下を実行します。

```bash
cd ~/projects/minutes-pipeline   # またはプロジェクトのパス
chmod +x scripts/push_to_github.sh
bash scripts/push_to_github.sh
```

初回は GitHub の認証（ユーザ名・パスワードまたはトークン）を求められる場合があります。

---

## 方法 B: コマンドを手動で実行

### 1. プロジェクトルートに移動

```bash
cd ~/projects/minutes-pipeline
```

### 2. Git リポジトリの有無を確認

```bash
git status
```

- **エラーになる場合**（リポジトリがない場合）  
  ```bash
  git init
  ```

### 3. リモートの設定

リモートが未設定の場合のみ実行します。

```bash
git remote add origin https://github.com/kmh-no3/minutes_pipeline.git
```

既に別のリモートが設定されている場合は、URL を差し替えます。

```bash
git remote set-url origin https://github.com/kmh-no3/minutes_pipeline.git
```

### 4. 変更をステージしてコミット

```bash
git add -A
git status   # 追加されるファイルを確認
git commit -m "Update: latest changes (docs, config, pipeline)"
```

※ コミットする変更がない場合は `git commit` は不要です。

### 5. メインブランチを main にしてプッシュ

```bash
git branch -M main
git push -u origin main
```

---

## 認証について

- **HTTPS** でプッシュする場合  
  - ユーザ名: GitHub のユーザ名  
  - パスワード: **Personal Access Token**（パスワードは使えません）  
  - Token の作成: GitHub → Settings → Developer settings → Personal access tokens

- **SSH** でプッシュする場合  
  - リモート URL を `git@github.com:kmh-no3/minutes_pipeline.git` に変更  
  - `git remote set-url origin git@github.com:kmh-no3/minutes_pipeline.git`  
  - SSH 鍵を GitHub に登録しておく

---

## 認証（方法4）でうまくいかない場合 → 最も確実な方法

PAT や SSH の設定でエラーになる場合は、**GitHub CLI（gh）でブラウザ認証**する方法が最も確実です。  
PAT のコピー・貼り付けや SSH 鍵の登録は不要で、ブラウザで GitHub にログインするだけで認証が完了します。

**手順の詳細**: [GitHubプッシュ_最も確実な方法_GitHub_CLI.md](./GitHubプッシュ_最も確実な方法_GitHub_CLI.md)

**流れの要約**:

1. **gh** をインストール（WSL なら `sudo apt install gh` の前に [同ドキュメント](./GitHubプッシュ_最も確実な方法_GitHub_CLI.md) のインストール手順を参照）
2. **`gh auth login`** を実行 → 「Login with a web browser」を選ぶ → ブラウザでコードを入力して認証（一度だけ）
3. リモートが HTTPS であることを確認: `git remote set-url origin https://github.com/kmh-no3/minutes_pipeline.git`
4. いつもどおり **`git push -u origin main`** または **`bash scripts/push_to_github.sh`**

---

## プッシュ後の確認

ブラウザで https://github.com/kmh-no3/minutes_pipeline を開き、ファイルが反映されているか確認してください。
