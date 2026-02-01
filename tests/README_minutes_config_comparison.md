# テスト用設定ファイル別・想定処理時間の比較

各 YAML は同じパイプライン（ASR → preprocess → summarize）を使用し、**summarize.engine: manual** のため要約はリクエストパック出力のみで LLM 呼び出しは行いません。処理時間の大部分は **ASR（Whisper）** で消費されます。

## 想定処理時間の比較表

| 設定ファイル | ASR モデル | デバイス | 計算精度 | 相対的な想定処理時間 | 目安（25分音声） | 目安（1時間音声） |
|-------------|------------|----------|----------|------------------------|------------------|-------------------|
| **minutes_tiny.yml**   | tiny     | CPU | int8  | **最短**               | 約 1〜2 分       | 約 2〜5 分        |
| **minutes_small.yml**  | small    | CPU | int8  | **短い**               | 約 2〜4 分       | 約 5〜10 分       |
| **minutes_base.yml**   | base     | CPU | int8  | **やや短い**           | 約 2〜5 分       | 約 6〜12 分       |
| **minutes_medium.yml** | medium   | CPU | int8  | **中程度**             | 約 8〜15 分      | 約 20〜40 分      |
| **minutes_large.yml**  | large-v3 | CPU | int8  | **長い**               | 約 15〜35 分     | 約 40〜90 分      |
| **minutes_dev.yml**    | large-v3 | **CUDA** | float16 | **短い（GPU 時）** | 約 1〜3 分       | 約 3〜8 分        |
| **minutes_dev_lowvram.yml** | large-v3 | **CUDA** | int8  | **短い（GPU・省VRAM）** | 約 2〜5 分       | 約 5〜15 分       |

- **目安**は CPU/GPU の性能や音声内容により変動します。実測値は環境ごとに計測してください。
- **minutes_dev.yml** は GPU 用のため、GPU がない環境では **minutes_large.yml** を使用してください（処理時間は「長い」になります）。
- **minutes_dev_lowvram.yml** は GPU + int8（VRAM 節約用）。float16 よりやや遅くなる場合がありますが、同じ GPU で large-v3 を動かす想定です。

## 設定別サマリ

| 設定ファイル | 用途・特徴 | 出力フォルダ例 |
|-------------|------------|-----------------|
| minutes_tiny.yml   | 最も軽量。速度優先・精度は低め。                           | `{date}_{stem}_tiny`   |
| minutes_small.yml  | 中程度の精度。速度と精度のバランス。                       | `{date}_{stem}_small`  |
| minutes_base.yml   | 軽量の1段階上。ASR base・CPU・int8。                       | `{date}_{stem}_base`   |
| minutes_medium.yml | 高精度。ASR medium・CPU・int8。                           | `{date}_{stem}_medium`  |
| minutes_large.yml  | 最高精度（CPU）。large-v3・CPU・int8。GPU なし環境向け。   | `{date}_{stem}_large`   |
| minutes_dev.yml    | 開発・高精度（GPU）。large-v3・CUDA・float16。              | `{date}_{stem}_gpu`     |
| minutes_dev_lowvram.yml | 開発・低VRAM（GPU）。large-v3・CUDA・int8。VRAM 不足・共有時用。 | `{date}_{stem}_gpu_lowvram` |

## 補足

- **preprocess**（辞書・ストップフレーズ）と **summarize**（manual 時のファイル出力）は、いずれの設定でも数秒〜十数秒程度とし、上記の目安には含めていません。
- 実測で処理時間を計測する場合は、パイプライン内で `asr` ステップの前後で時刻を記録するか、既存の `run_metadata.json` 等を利用してください。
