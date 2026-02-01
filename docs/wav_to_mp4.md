# WAVE 内の .wav を .mp4 に変換する

`tests/data/input` 以下の **WAVE** フォルダ直下にある `.wav` を、ffmpeg で `.mp4`（AAC 音声）に変換します。**元の .wav は削除しません。**

## 前提

- **ffmpeg** がインストールされ、PATH に入っていること。
  - WSL/Ubuntu: `sudo apt install ffmpeg`
  - Windows: [ffmpeg](https://ffmpeg.org/) をインストールし PATH に追加

## 実行方法

### 方法1: Python スクリプト（推奨・Windows/WSL 共通）

プロジェクトルートで:

```bash
python3 wav_to_mp4.py
# または別の基準ディレクトリを指定
python3 wav_to_mp4.py /path/to/input
```

実行結果はコンソールと `wav_to_mp4_log.txt` に出力されます。

### 方法2: Bash スクリプト（WSL/Linux）

```bash
chmod +x wav_to_mp4.sh
./wav_to_mp4.sh
# または
./wav_to_mp4.sh /path/to/input
```

## 出力

- 各 `.wav` と同じ WAVE フォルダ内に、同じベース名の `.mp4` が作成されます。
- 音声コーデック: AAC、ビットレート: 192kbps。
- 元の `.wav` はそのまま残ります。
