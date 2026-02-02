# 方法4: GitHub 認証の詳細（HTTPS と SSH）

リモート `https://github.com/kmh-no3/minutes_pipeline.git` へプッシュする際の認証方法を、HTTPS（Personal Access Token）と SSH の両方について詳しく説明します。

---

## 目次

1. [HTTPS + Personal Access Token（PAT）](#1-https--personal-access-tokenpat)
2. [SSH 鍵認証](#2-ssh-鍵認証)
3. [どちらを選ぶか・切り替え](#3-どちらを選ぶか切り替え)

---

## 1. HTTPS + Personal Access Token（PAT）

GitHub では**通常のパスワードでプッシュできません**。代わりに **Personal Access Token（PAT）** を使います。

### 1.1 PAT の作成手順

1. **GitHub にログイン**し、右上のアイコン → **Settings** を開く。
2. 左メニュー最下部の **Developer settings** をクリック。
3. **Personal access tokens** → **Tokens (classic)** を選択。
4. **Generate new token** → **Generate new token (classic)** をクリック。
5. 以下を設定する：
   - **Note**: 用途が分かる名前（例: `minutes-pipeline push`）。
   - **Expiration**: 有効期限（90日 / 1年 / 無期限など）。
   - **Scopes**: 少なくとも **`repo`** にチェック（プッシュ・プルに必要）。  
     必要に応じて `workflow` なども付与。
6. **Generate token** をクリック。
7. **表示されたトークン（`ghp_...`）を必ずコピーして安全な場所に保存**する。  
   この画面を離れると再表示できません。

### 1.2 リモート URL の確認（HTTPS のまま）

現在 HTTPS の場合はそのままで問題ありません。

```bash
git remote -v
# origin  https://github.com/kmh-no3/minutes_pipeline.git (fetch)
# origin  https://github.com/kmh-no3/minutes_pipeline.git (push)
```

HTTPS に戻したい場合（SSH から切り替える場合）:

```bash
git remote set-url origin https://github.com/kmh-no3/minutes_pipeline.git
```

### 1.3 プッシュ時に PAT を入力する

初回プッシュ（または認証情報が未保存のとき）で、プロンプトが出ます。

- **Username**: GitHub のユーザ名（例: `kmh-no3`）。
- **Password**: **通常のパスワードではなく、作成した PAT をそのまま貼り付け**。

```bash
git push -u origin main
# Username for 'https://github.com': kmh-no3
# Password for 'https://kmh-no3@github.com': （ここに PAT を貼り付け）
```

### 1.4 認証情報を保存する（毎回入力しない）

#### Windows（Git Credential Manager が入っている場合）

一度 PAT でログインすると、Credential Manager に保存され、次回以降は自動で使われます。

- 保存先の確認・削除: **コントロールパネル** → **資格情報マネージャー** → **Windows の資格情報** で `git:https://github.com` を確認できます。

#### WSL（Linux）

キャッシュで一定時間記憶させる例（15 分）:

```bash
git config --global credential.helper 'cache --timeout=900'
```

ディスクに保存する例（平文で `~/.git-credentials` に書くため、利用は自己責任で）:

```bash
git config --global credential.helper store
# 次回 git push で PAT を入力すると、以降は保存されて自動入力される
```

#### macOS

多くの環境では Git に付属の credential helper が使われ、キーチェーンに保存されます。  
必要なら `credential.helper` を `osxkeychain` に設定します。

### 1.5 よくあるエラー（HTTPS）

| 現象 | 原因・対処 |
|------|------------|
| `Authentication failed` | パスワード欄に**通常のパスワード**を入れている → **PAT** を入れる。 |
| `Support for password authentication was removed` | 同上。GitHub はパスワード認証を廃止しているため、必ず PAT を使用。 |
| `failed to push some refs`（認証とは別） | リモートが先行している場合は `git pull --rebase` してから再度 `git push`。 |

---

## 2. SSH 鍵認証

SSH を使うと、**鍵を登録しておくだけでパスワード（PAT）を毎回入力しなくてよい**ことが多いです。

### 2.1 既存の SSH 鍵があるか確認する

```bash
# WSL / Linux / macOS
ls -la ~/.ssh
# id_ed25519 と id_ed25519.pub、または id_rsa と id_rsa.pub があれば既存
```

Windows（PowerShell）で OpenSSH を使っている場合:

```powershell
dir $env:USERPROFILE\.ssh
```

`.pub` が付く方が**公開鍵**、付かない方が**秘密鍵**です。秘密鍵は絶対に他人に渡さないでください。

### 2.2 新しい SSH 鍵を生成する（ない場合）

WSL / Linux / macOS:

```bash
ssh-keygen -t ed25519 -C "your_email@example.com"
# ファイル名は Enter でデフォルト（~/.ssh/id_ed25519）でよい
# パスフレーズを聞かれたら任意（空でも可。付けるとより安全）
```

Windows（PowerShell）で OpenSSH がある場合:

```powershell
ssh-keygen -t ed25519 -C "your_email@example.com"
# 保存先はデフォルトの %USERPROFILE%\.ssh\id_ed25519 でよい
```

古い環境で `ed25519` が使えない場合は `-t rsa -b 4096` で RSA 鍵を生成できます。

### 2.3 公開鍵を GitHub に登録する

1. **公開鍵の内容をコピーする**

   WSL / Linux / macOS:

   ```bash
   cat ~/.ssh/id_ed25519.pub
   # 表示された 1 行全体をコピー（ssh-ed25519 AAAA... your_email@example.com）
   ```

   Windows（PowerShell）:

   ```powershell
   Get-Content $env:USERPROFILE\.ssh\id_ed25519.pub
   ```

2. **GitHub** → 右上アイコン → **Settings** → 左の **SSH and GPG keys**。
3. **New SSH key** をクリック。
4. **Title**: 識別用の名前（例: `WSL Ubuntu` や `My PC`）。
5. **Key type**: Authentication Key のまま。
6. **Key**: コピーした公開鍵（1 行全体）を貼り付け。
7. **Add SSH key** で保存。

### 2.4 リモート URL を SSH に変更する

```bash
git remote set-url origin git@github.com:kmh-no3/minutes_pipeline.git
git remote -v
# origin  git@github.com:kmh-no3/minutes_pipeline.git (fetch)
# origin  git@github.com:kmh-no3/minutes_pipeline.git (push)
```

### 2.5 SSH の接続テスト

```bash
ssh -T git@github.com
```

成功すると、例えば次のように表示されます:

```
Hi kmh-no3! You've successfully authenticated, but GitHub does not provide shell access.
```

初回は `Are you sure you want to continue connecting (yes/no)?` と出るので **yes** と入力します。

### 2.6 プッシュする

```bash
git push -u origin main
```

PAT の入力は不要で、SSH 鍵（とパスフレーズがあればそれだけ）で認証されます。

### 2.7 ssh-agent に鍵を登録する（パスフレーズを毎回聞かれないように）

WSL / Linux（セッションごと）:

```bash
eval "$(ssh-agent -s)"
ssh-add ~/.ssh/id_ed25519
# パスフレーズを 1 回入力すると、そのターミナルでは記憶される
```

Windows（PowerShell）で OpenSSH の ssh-agent を使う場合:

```powershell
Get-Service ssh-agent | Set-Service -StartupType Manual
Start-Service ssh-agent
ssh-add $env:USERPROFILE\.ssh\id_ed25519
```

### 2.8 よくあるエラー（SSH）

| 現象 | 原因・対処 |
|------|------------|
| `Permission denied (publickey)` | 公開鍵が GitHub に登録されていない、または別の鍵を使っている → 登録した鍵の `~/.ssh/id_ed25519.pub` と一致するか確認。`ssh -T git@github.com` で再確認。 |
| `Could not resolve hostname github.com` | ネットワークや DNS の不調 → ブラウザで github.com にアクセスできるか確認。 |
| WSL で Windows の鍵を使いたい | Windows の `id_ed25519` を WSL から参照する方法もあるが、パスの扱いが複雑。多くの場合は WSL 用に別鍵を用意する方が簡単。 |

---

## 3. どちらを選ぶか・切り替え

### 選び方の目安

| 方式 | 向いている人 |
|------|----------------|
| **HTTPS + PAT** | トークン発行だけですぐ使いたい、会社のプロキシで HTTPS しか通る、など。 |
| **SSH** | 複数リポジトリをよく触る、パスワードを打ちたくない、鍵管理に慣れている、など。 |

### 現在のリモート URL の確認

```bash
git remote get-url origin
```

- `https://github.com/...` → HTTPS（PAT で認証）。
- `git@github.com:...` → SSH（鍵で認証）。

### 切り替えコマンド

**HTTPS に設定する:**

```bash
git remote set-url origin https://github.com/kmh-no3/minutes_pipeline.git
```

**SSH に設定する:**

```bash
git remote set-url origin git@github.com:kmh-no3/minutes_pipeline.git
```

切り替えたあと、次回の `git push` から新しい認証方式が使われます。

---

## 参考リンク

- [GitHub: Creating a personal access token](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/creating-a-personal-access-token)
- [GitHub: Connecting to GitHub with SSH](https://docs.github.com/en/authentication/connecting-to-github-with-ssh)
