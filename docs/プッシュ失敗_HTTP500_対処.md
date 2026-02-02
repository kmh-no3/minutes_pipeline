# プッシュ失敗（HTTP 500 / 2.18 GiB）の原因と対処

## 原因

1. **GitHub の 1 回あたりのプッシュ上限**  
   GitHub は **1 回のプッシュで約 2 GiB まで** という制限があります。  
   今回のプッシュは **2.18 GiB** だったため、制限を超えて **HTTP 500** や `the remote end hung up unexpectedly` が発生しています。

2. **大きなファイルがコミットに含まれている**  
   **`tests/data/input/`** にテスト用の mp4・wav（約 6,500 ファイル）が入っており、これが **`.gitignore` に含まれておらず** コミットされていました。  
   その結果、プッシュ対象が 2.18 GiB になっていました。

## 実施した対応

- **`.gitignore` に `tests/data/input/` を追加**  
  今後このフォルダはコミットされません。  
  （`tests/data/README.md` にも「リポジトリにはコミットせず」とある運用に合わせています。）

## あなたがやること（WSL のターミナルで実行）

**既存のコミット履歴** から `tests/data/input/` と `tests/output/` を消し、プッシュサイズを 2 GiB 未満にする必要があります。  
以下は **WSL の bash** でプロジェクトルート（`~/projects/minutes-pipeline`）にいる状態で実行してください。

### 方法 A: スクリプトで一括実行（推奨）

```bash
cd ~/projects/minutes-pipeline
chmod +x scripts/remove_large_tests_from_history.sh
bash scripts/remove_large_tests_from_history.sh
```

スクリプトが、履歴からの削除・`refs/original` 削除・`git gc` まで一括で行います。  
最後に `git count-objects -vH` の結果が表示されるので、**size-pack が 2 GiB 未満**になっているか確認してください。

**「Cannot rewrite branches: You have unstaged changes.」と出た場合**  
未コミットの変更があると `filter-branch` は実行されません。次のどちらかを実行してから、再度スクリプトを実行してください。

- 変更をコミットする: `git add -A` → `git commit -m "chore: 履歴削減前に一時コミット"`
- 変更を一時退避する: `git stash push -m "before remove_large_tests_from_history"`（実行後に `git stash pop` で戻せます）

### 方法 B: コマンドを手動で実行

#### 1. 履歴から tests/data/input と tests/output を削除する

```bash
cd ~/projects/minutes-pipeline

export FILTER_BRANCH_SQUELCH_WARNING=1
git filter-branch --force --index-filter \
  'git rm -r --cached --ignore-unmatch tests/data/input tests/output' \
  --prune-empty HEAD
```

途中で「Cannot create a new backup」と出た場合は、上記の `export FILTER_BRANCH_SQUELCH_WARNING=1` を先に実行してから再度実行します。

#### 2. 不要なオブジェクトを削除する

```bash
rm -rf .git/refs/original/
git reflog expire --expire=now --all
git gc --prune=now --aggressive
```

### 3. 変更をコミットする（.gitignore の変更がまだなら・方法 B の場合）

```bash
git add .gitignore
git status   # tests/data/input/ が untracked のままであることを確認
git commit -m "chore: ignore tests/data/input (large media, avoid GitHub push limit)"
```

※ すでに `.gitignore` の変更だけをコミットしている場合はこのステップは不要です。

### 4. プッシュする

```bash
git push -u origin main
```

これでプッシュサイズが 2 GiB を下回り、GitHub への反映が完了する想定です。

## 参考

- [GitHub: Troubleshooting the 2 GiB push limit](https://docs.github.com/en/get-started/using-git/troubleshooting-the-2-gb-push-limit)
- テスト用 mp4/wav はローカルの `tests/data/input/` に残したまま利用できます。リポジトリには含めません。
