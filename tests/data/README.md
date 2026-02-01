# テストデータ

パイプラインのテスト・回帰評価用のデータを格納します。

## 入力動画（mp4）

- **格納場所**: `tests/data/input/`
- テスト用の mp4 ファイルをここに置いてください。
- 実行例（プロジェクトルートから。出力は `tests/output/` に納まり、examples は鋳型のため使用しない）:
  ```bash
  mpipe run tests/data/input/meeting.mp4 --config tests/minutes_dev.yml
  ```
  開発環境では `--config tests/minutes_dev.yml` を推奨（GPU で速い）。GPU がなければ `--config tests/minutes_large.yml` を使ってください。
  または、プロジェクトフォルダを `tests/data` 相当にしたうえで `input/` を指定しても構いません。

※ 実際の mp4 は容量が大きいため、リポジトリにはコミットせず `.gitignore` で除外する運用も可能です。
