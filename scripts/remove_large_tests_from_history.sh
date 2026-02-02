#!/bin/bash
# 履歴から tests/data/input と tests/output を削除し、プッシュサイズを 2 GiB 未満にする
# 実行前に必ずプロジェクトルート（minutes-pipeline）で実行すること
set -e
cd "$(dirname "$0")/.."

# 未コミットの変更があると filter-branch が拒否するため、事前チェック
if [ -n "$(git status --porcelain)" ]; then
  echo "エラー: 未コミットの変更があります。"
  echo "履歴の書き換えを行うため、作業ツリーはクリーンである必要があります。"
  echo ""
  echo "対処方法（どちらか実行してから、再度このスクリプトを実行してください）:"
  echo "  (1) 変更をコミットする:"
  echo "      git add -A"
  echo "      git commit -m \"chore: 履歴削減前に一時コミット\""
  echo ""
  echo "  (2) 変更を一時退避する:"
  echo "      git stash push -m \"before remove_large_tests_from_history\""
  echo "      （スクリプト実行後に git stash pop で戻せます）"
  exit 1
fi

echo "=== 現在のオブジェクトサイズ確認 ==="
git count-objects -vH

echo ""
echo "=== 履歴から tests/data/input と tests/output を削除します（書き換え） ==="
export FILTER_BRANCH_SQUELCH_WARNING=1
git filter-branch --force --index-filter \
  'git rm -r --cached --ignore-unmatch tests/data/input tests/output' \
  --prune-empty HEAD

echo ""
echo "=== バックアップ用 refs を削除 ==="
rm -rf .git/refs/original/

echo ""
echo "===  reflog を期限切れにし、ガベージコレクト ==="
git reflog expire --expire=now --all
git gc --prune=now --aggressive

echo ""
echo "=== 削減後のサイズ確認 ==="
git count-objects -vH
echo ""
echo "size-pack が 2 GiB 未満になっていれば、git push -u origin main でプッシュできます。"
