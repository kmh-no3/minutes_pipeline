#!/bin/bash
# GitHub へ最新の変更をコミット・プッシュするスクリプト
set -e
cd "$(dirname "$0")/.."
REPO_URL="https://github.com/kmh-no3/minutes_pipeline.git"

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "Git リポジトリがありません。git init を実行します。"
  git init
fi

# リモートが未設定なら追加
if ! git remote get-url origin >/dev/null 2>&1; then
  git remote add origin "$REPO_URL"
  echo "リモート origin を追加しました: $REPO_URL"
fi

# 現在のリモートURLを表示
echo "現在の origin: $(git remote get-url origin)"

# 変更をステージ
git add -A
STATUS=$(git status --porcelain)
if [ -n "$STATUS" ]; then
  git commit -m "Update: latest changes (docs, config, pipeline)"
  echo "コミットしました。"
else
  echo "コミットする変更はありません。"
fi

# メインブランチを main に統一してプッシュ
git branch -M main
git push -u origin main
echo "プッシュ完了: $REPO_URL"
