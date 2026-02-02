# 最も確実なプッシュ方法: GitHub CLI（gh）でブラウザ認証

PAT（Personal Access Token）や SSH 鍵の設定でうまくいかない場合、**GitHub CLI（gh）** を使うと、**ブラウザで GitHub にログインするだけ**で認証が完了し、その後の `git push` が確実に動くことが多いです。

---

## なぜこれが確実か

- **PAT のコピー・貼り付けが不要**（トークンを手動で作って入力する必要がない）
- **SSH 鍵の生成・登録が不要**
- **ブラウザで「Authorize」するだけ**で Git の認証が通る
- GitHub 公式が提供しており、多くの環境で動作実績がある

---

## 手順の流れ

1. GitHub CLI（gh）をインストールする
2. `gh auth login` でブラウザ認証する（一度だけ）
3. いつもどおり `git push` する

---

## 1. GitHub CLI（gh）のインストール

### WSL（Ubuntu）で使う場合

プロジェクトが WSL のパス（`~/projects/minutes-pipeline`）にあるときは、**WSL 側に gh を入れます**。

```bash
# 公式の方法（推奨）
type -p curl >/dev/null || (sudo apt update && sudo apt install curl -y)
curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | sudo dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg
sudo chmod go+r /usr/share/keyrings/githubcli-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | sudo tee /etc/apt/sources.list.d/github-cli.list > /dev/null
sudo apt update
sudo apt install gh -y
```

インストール確認:

```bash
gh --version
```

### Windows（PowerShell）で使う場合

プロジェクトを Windows のパス（例: `C:\Users\user\projects\minutes-pipeline`）にクローンして使う場合は、**Windows 側に gh を入れます**。

- **winget**（Windows 10/11 に標準）:
  ```powershell
  winget install --id GitHub.cli -e
  ```
- または [GitHub CLI の公式ページ](https://cli.github.com/) からインストーラーをダウンロードして実行。

インストール後、**新しいターミナル**を開いて確認:

```powershell
gh --version
```

---

## 2. 認証（一度だけやればよい）

### WSL で実行する場合

WSL のターミナルで:

```bash
gh auth login
```

表示される質問には次のように答えます。

1. **What account do you want to log into?**  
   → **GitHub.com** を選択（矢印キーで選んで Enter）

2. **What is your preferred protocol for Git operations?**  
   → **HTTPS** を選択（矢印キーで選んで Enter）

3. **Authenticate Git with your GitHub credentials?**  
   → **Yes** を選択

4. **How would you like to authenticate GitHub CLI?**  
   → **Login with a web browser** を選択（矢印キーで選んで Enter）

5. 画面に **one-time code**（英数字のコード）が表示されるので、それをコピーして Enter。

6. **ブラウザが開く**（開かない場合は表示された URL をブラウザで開く）。

7. ブラウザで GitHub にログインしていなければログインし、**表示されたコードを入力**して **Authorize** をクリック。

8. ターミナルに「Successfully authenticated」と出れば完了です。

### Windows（PowerShell）で実行する場合

PowerShell で同じコマンドを実行します。

```powershell
gh auth login
```

質問の内容と選び方は上と同じです（GitHub.com → HTTPS → Yes → Login with a web browser → コードをブラウザで入力 → Authorize）。

---

## 3. リモートを HTTPS にしておく（推奨）

gh で認証すると、**HTTPS** で Git 操作するときにその認証が使われます。リモートが SSH のままになっている場合は HTTPS に戻します。

```bash
git remote set-url origin https://github.com/kmh-no3/minutes_pipeline.git
git remote -v
# origin  https://github.com/kmh-no3/minutes_pipeline.git (fetch)
# origin  https://github.com/kmh-no3/minutes_pipeline.git (push)
```

---

## 4. プッシュする

あとは通常どおりコミットしてプッシュします。

### WSL でプロジェクトがある場合

```bash
cd ~/projects/minutes-pipeline
git add -A
git status
git commit -m "Update: latest changes"   # 変更がある場合のみ
git branch -M main
git push -u origin main
```

### スクリプトで一括実行する場合

```bash
cd ~/projects/minutes-pipeline
bash scripts/push_to_github.sh
```

**PAT やパスワードの入力は求められません**。gh が認証を担当しているためです。

---

## 5. うまくいかないときの確認

### 認証状態の確認

```bash
gh auth status
```

「Logged in to github.com as ユーザ名」と出ていれば OK です。

### Git に gh の認証を使わせる

gh は通常、Git の credential helper を自動で設定します。もし `git push` でまだ認証を聞かれる場合は、次を実行します。

**WSL:**

```bash
gh auth setup-git
```

**Windows（PowerShell）:**

```powershell
gh auth setup-git
```

その後、もう一度 `git push -u origin main` を試します。

### リモート URL の確認

必ず HTTPS になっているか確認します。

```bash
git remote get-url origin
# https://github.com/kmh-no3/minutes_pipeline.git であること
```

SSH（`git@github.com:...`）になっている場合は、前述の「3. リモートを HTTPS にしておく」のコマンドで HTTPS に変更してください。

---

## まとめ

| ステップ | やること |
|----------|----------|
| 1 | WSL なら WSL に、Windows なら Windows に **gh** をインストール |
| 2 | **gh auth login** で「Login with a web browser」を選び、ブラウザで認証（一度だけ） |
| 3 | リモートが HTTPS か確認し、必要なら **git remote set-url origin https://github.com/kmh-no3/minutes_pipeline.git** |
| 4 | **git push -u origin main** または **bash scripts/push_to_github.sh** でプッシュ |

この方法なら、PAT の作成・コピーや SSH 鍵の設定をせずに、ブラウザのログインだけで確実にプッシュできるようになります。
