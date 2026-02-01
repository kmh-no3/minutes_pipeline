# minutes_dev.yml の見積もりと端末スペック確認

## minutes_dev.yml の設定

| 項目 | 値 |
|------|-----|
| ASR モデル | **large-v3**（最大サイズ） |
| デバイス | **cuda**（GPU） |
| 計算精度 | float16 |
| 想定 | **GPU あり環境**。GPU なしなら `minutes_large.yml`（CPU）を使う前提。 |

---

## 想定処理時間の目安

**テスト音声 B-0002 は約 25 分です。**

| 環境 | 25分音声の目安 | 1時間音声の目安 |
|------|----------------|------------------|
| **GPU が使えている場合**（CUDA 利用） | **約 3〜15 分** | **約 8〜30 分** |
| **GPU が使えていない場合**（実質 CPU や large 相当） | **約 40〜90 分以上** | **約 2〜4 時間以上** |

### 6 時間以上かかった場合に考えられること

- **CUDA が使えていなかった**  
  `device: "cuda"` のままでも、ドライバ・CUDA 未導入や WSL 側で GPU 未認識だと、エラーになるか別経路で非常に遅い挙動になることがあります。
- **実際には minutes_large.yml（CPU・large-v3）で実行していた**  
  CPU の large-v3 は重く、25 分音声で 1〜2 時間、環境によってはそれ以上かかることがあります。6 時間は極端ですが、スペックや負荷次第ではあり得ます。
- **GPU が極端に弱い／共有・制限されている**  
  内蔵 GPU のみ・メモリ不足・サーマルスロットリングなどで、実質 CPU 並みになる場合があります。

**結論:** 正常に **GPU（CUDA）が使えていれば**、25 分音声で **十数分〜30 分程度** が目安です。6 時間は **GPU が効いていないか、別設定（CPU の large）で動いていた**可能性が高いです。

---

## minutes_dev_lowvram.yml の想定処理時間

| 項目 | 値 |
|------|-----|
| ASR モデル | large-v3（minutes_dev.yml と同じ） |
| デバイス | cuda（GPU） |
| 計算精度 | **int8**（VRAM 節約・GPU 共有時向け） |

| 音声長 | 想定処理時間（GPU 使用時） |
|--------|----------------------------|
| **25 分音声**（B-0002 等） | **約 2〜5 分**（余裕を見て 5〜15 分） |
| **1 時間音声** | **約 5〜15 分**（余裕を見て 15〜30 分） |

- minutes_dev.yml（float16）より **やや遅い**ことがありますが、同じ GPU で large-v3 を動かすため、CPU の minutes_large.yml よりは **かなり短い**です。
- 初回のみ large-v3 モデルのダウンロードで **数分〜十数分** が加わることがあります。

---

## 本端末のスペック確認（WSL 上で実行）

**WSL のターミナル**で、プロジェクトルートに移動してから以下を実行してください。

### 1. スペック一括取得（推奨）

```bash
cd /home/user/projects/minutes-pipeline
source .venv/bin/activate
python3 tests/collect_specs.py
```

- 結果は **`tests/output/specs_report.txt`** に出力されます。
- 同じ内容がターミナルにも表示されます。
- 中身: CPU（lscpu）、コア数、メモリ、nvidia-smi、faster-whisper の CUDA/CPU 利用可否。

### 2. 手動で確認する場合

```bash
# CPU
lscpu
nproc

# メモリ
free -h

# GPU（NVIDIA ドライバが入っていれば）
nvidia-smi

# faster-whisper が GPU を使えるか
python3 -c "
from faster_whisper import WhisperModel
m = WhisperModel('tiny', device='cuda', compute_type='float16')
print('CUDA: OK')
del m
"
```

- `nvidia-smi` で GPU 名とメモリが表示され、最後の Python がエラーなく `CUDA: OK` と出れば、**minutes_dev.yml は GPU で動く**想定です。

---

## 次回実行の見積もりの決め方

1. 上記で **CUDA: OK** と確認できた場合  
   - **25 分音声:** 余裕を見て **15〜30 分** 程度で見積もる。  
   - 初回は large-v3 モデル DL で **数分〜十数分** が加わる場合あり。

2. **CUDA が使えない**場合  
   - minutes_dev.yml は `device: cuda` のためエラーになる可能性が高いです。  
   - その場合は **minutes_large.yml**（CPU・large-v3）を使い、**25 分音声で 1〜2 時間以上** を目安にすると安全です。睡眠時間に差し掛かるなら、**夜は small / base にしておく**方が無難です。

3. **前回 6 時間かかった**ことを踏まえると  
   - 次も同じ環境なら、**GPU 確認を先にすること**と、**最初は small や base で時間を計ってから dev を試す**ことを推奨します。

---

## まとめ

| 確認項目 | やること |
|----------|----------|
| スペックと CUDA | WSL で `python3 tests/collect_specs.py` を実行し、`tests/output/specs_report.txt` を確認 |
| GPU が使える場合 | 25 分音声 → **約 15〜30 分**（初回はモデル DL で +数分）で見積もり |
| GPU が使えない場合 | **minutes_large.yml** を使い、25 分音声で **1〜2 時間以上** を想定。睡眠前は small/base 推奨 |
