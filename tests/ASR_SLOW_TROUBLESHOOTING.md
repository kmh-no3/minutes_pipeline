# ASR（minutes_base.yml 等）が目安より遅いときの原因と対処

## 想定している音声

- テストデータ B-0002: **約25分**の音声（会議）
- 目安「25分音声で base 約 2〜5 分」は **faster-whisper** 使用時のおおよその値です

---

## 原因として考えられるもの（優先度順）

### 1. **openai-whisper が使われている（最も有力）**

パイプラインは **faster-whisper** を優先し、import に失敗した場合だけ **openai-whisper** にフォールバックします。

- **faster-whisper**（CTranslate2）: 最適化・int8 対応で **速い**
- **openai-whisper**: 同じモデルでも **2〜5 倍以上遅くなりやすい**（int8 未使用・実装の差）

`pip install -e ".[asr]"` だけだと `pyproject.toml` の asr 依存は **openai-whisper のみ**なので、faster-whisper が入っていないと遅い方で動きます。

**確認（どちらのエンジンか）:**

```bash
python -c "
try:
    from faster_whisper import WhisperModel
    print('ASR: faster-whisper (速い方)')
except ImportError:
    print('ASR: faster-whisper は未インストール')
try:
    import whisper
    print('ASR: openai-whisper は利用可能 (フォールバック・遅くなりやすい)')
except ImportError:
    print('ASR: openai-whisper も未インストール')
"
```

**対処:** faster-whisper を入れて、再度実行する。

```bash
pip install faster-whisper
# その後
mpipe run tests/data/input/SPREDS-D1.ver1.3.ja/ver1.3/ja/mixed/WAVE/B-0002.wav --config tests/minutes_base.yml
```

---

### 2. **PC スペック（CPU・メモリ）**

目安は「そこそこ性能のある CPU」を想定しています。

- **ノート PC / 省電力 CPU（U 系など）**: 同じ base モデルでも 1.5〜2 倍以上かかることがあります
- **コア数・周波数**: Whisper は CPU 負荷が高く、コア数・ターボ周波数が低いと遅くなります
- **メモリ不足**: スワップが出るとさらに遅くなります

「スペックが足りない」というより、「目安は中〜高めのデスクトップを想定している」と考えてください。スペックが低いほど「目安の 2 倍かかってもおかしくない」程度の余裕を持たせるとよいです。

---

### 3. **初回実行（モデルダウンロード・コールドスタート）**

- **初回のみ**: `base` モデルのダウンロードで数十秒〜数分かかります
- モデル読み込みのコールドスタートも初回は重くなりがちです  
→ 2 回目以降の同じ音声・同じ設定で再度計測すると差が分かります

---

### 4. **WSL で実行している場合**

パスから WSL 利用と推測される場合:

- **Windows 側のドライブ（/mnt/c/...）のファイルを読む**: I/O が遅く、ASR 前後の読み書きがボトルネックになることがあります  
  → 音声ファイルを WSL 内のホーム（例: `/home/user/projects/...`）に置いて実行すると改善する場合があります
- **WSL2 の CPU 割り当て**: ホストの負荷で CPU が制限されると、処理時間が伸びます

---

### 5. **サーマルスロットリング（ノート PC）**

- 負荷が続くと CPU が絞られ、後半になるほど遅くなることがあります
- 冷却しやすい環境（台の上・エアコンなど）で再実行すると差が出ることがあります

---

## まとめ

| 確認項目           | やること |
|--------------------|----------|
| どちらのエンジンか | 上記の `python -c "..."` で faster-whisper / openai-whisper を確認 |
| 遅い方だった場合   | `pip install faster-whisper` で faster-whisper を導入して再実行 |
| すでに faster-whisper | CPU スペック・初回DL・WSL・サーマルを疑い、2 回目以降の時間や別マシンで比較 |

まずは **「faster-whisper が使われているか」** を上記コマンドで確認し、未導入ならインストールしてから再度 `minutes_base.yml` で計測するのがおすすめです。
