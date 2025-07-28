import asyncio
import os
import queue
import tempfile
import threading
import logging

from faster_whisper import WhisperModel
import numpy as np
from scipy.io.wavfile import write
import sounddevice as sd

# ==== ログ設定 ====
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

# ==== モデル選択 ====
MODEL_LIST = {
    "1": "tiny",
    "2": "small",
    "3": "medium",
    "4": "large-v2",
    "5": "large-v3",
    "6": "deepdml/faster-whisper-large-v3-turbo-ct2",
}

print("モデル選択：")
for k, v in MODEL_LIST.items():
    print(f"{k}: {v}")
model_key = input("番号を入力してください: ").strip()
model_name = MODEL_LIST.get(model_key, "tiny")
logging.info(f"モデル: {model_name} を使用")
model = WhisperModel(model_name, device="cuda", compute_type="float16")

# ==== 音声設定 ====
SAMPLERATE = 16000
CHUNK_DURATION = 0.5  # 秒
CHUNK_SIZE = int(SAMPLERATE * CHUNK_DURATION)
CHANNELS = 1

# ==== 無音検出パラメータ ====
SILENT_THRESHOLD = 5  # RMS
SPEECH_START_THRESHOLD = 50  # 話し始めのRMS
MAX_SILENCE_CHUNKS = 4  # 無音が続いたら話し終わりと判断

# ==== Queue ====
record_queue = queue.Queue()

# ==== 状態管理 ====
speaking = False
silence_chunks = 0
buffer = []
last_rms = 0

# ==== 音声処理関数 ====
def is_silent(chunk):
    rms = np.sqrt(np.mean(chunk.astype(np.float32) ** 2))
    return rms < SILENT_THRESHOLD

def has_started_speaking(chunk):
    global last_rms
    rms = np.sqrt(np.mean(chunk.astype(np.float32) ** 2))
    triggered = rms > SPEECH_START_THRESHOLD and last_rms < SPEECH_START_THRESHOLD
    last_rms = rms
    return triggered

def process_audio(chunks):
    logging.info("🔁 認識中...")
    audio_np = np.concatenate(chunks, axis=0)
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        write(tmp.name, SAMPLERATE, audio_np)
        tmp_path = tmp.name

    segments, _ = model.transcribe(tmp_path, language="ja", vad_filter=True)
    for seg in segments:
        print(f"[{seg.start:.1f}s → {seg.end:.1f}s] {seg.text.strip()}")

    os.remove(tmp_path)

# ==== 録音スレッド ====
def record_stream():
    def callback(indata, frames, time_info, status):
        if status:
            logging.warning(f"[!] Status: {status}")
        record_queue.put(indata.copy())

    with sd.InputStream(callback=callback, samplerate=SAMPLERATE,
                        blocksize=CHUNK_SIZE, channels=CHANNELS, dtype='int16'):
        while True:
            sd.sleep(100)

# ==== メイン処理 ====
async def main_loop():
    global speaking, silence_chunks, buffer
    print("🎙️ 音声入力待機中... (Ctrl+Cで終了)")

    while True:
        chunk = await asyncio.to_thread(record_queue.get)

        if has_started_speaking(chunk) and not speaking:
            logging.info("🎤 話し始めを検出")
            speaking = True
            buffer = [chunk]
            silence_chunks = 0
        elif speaking:
            buffer.append(chunk)
            if is_silent(chunk):
                silence_chunks += 1
                if silence_chunks >= MAX_SILENCE_CHUNKS:
                    logging.info("🛑 話し終わり → 文字起こし")
                    await asyncio.to_thread(process_audio, buffer)
                    speaking = False
                    buffer = []
            else:
                silence_chunks = 0

# ==== エントリーポイント ====
async def main():
    threading.Thread(target=record_stream, daemon=True).start()
    await main_loop()

try:
    asyncio.run(main())
except KeyboardInterrupt:
    print("\n🛑 停止しました。")
