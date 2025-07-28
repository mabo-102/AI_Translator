import asyncio
import logging
import os
import queue
import tempfile
import threading

import flet as ft
import numpy as np
import sounddevice as sd
from faster_whisper import WhisperModel
from scipy.io.wavfile import write

# ログ設定
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")

# 音声パラメータ
SAMPLERATE = 16000
CHUNK_DURATION = 0.5
CHUNK_SIZE = int(SAMPLERATE * CHUNK_DURATION)
CHANNELS = 1

SILENT_THRESHOLD = 5
SPEECH_START_THRESHOLD = 50
MAX_SILENCE_CHUNKS = 4

# Queueと状態
record_queue = queue.Queue()
speaking = False
silence_chunks = 0
buffer = []
last_rms = 0
model_ref = {"model": None}


def is_silent(chunk):
    rms = np.sqrt(np.mean(chunk.astype(np.float32) ** 2))
    return rms < SILENT_THRESHOLD


def has_started_speaking(chunk):
    global last_rms
    rms = np.sqrt(np.mean(chunk.astype(np.float32) ** 2))
    triggered = rms > SPEECH_START_THRESHOLD and last_rms < SPEECH_START_THRESHOLD
    last_rms = rms
    return triggered


def process_audio(chunks, append_result):
    logging.info("🔁 認識中...")
    audio_np = np.concatenate(chunks, axis=0)

    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        write(tmp.name, SAMPLERATE, audio_np)
        tmp_path = tmp.name

    segments, _ = model_ref["model"].transcribe(tmp_path, language="ja", vad_filter=True)
    for seg in segments:
        append_result(f"[{seg.start:.1f}s → {seg.end:.1f}s] {seg.text.strip()}")

    os.remove(tmp_path)


def record_stream():
    def callback(indata, frames, time_info, status):
        if status:
            logging.warning(f"[!] Status: {status}")
        record_queue.put(indata.copy())

    with sd.InputStream(
        callback=callback,
        samplerate=SAMPLERATE,
        blocksize=CHUNK_SIZE,
        channels=CHANNELS,
        dtype='int16'
    ):
        while True:
            sd.sleep(100)


async def main_loop(append_result):
    global speaking, silence_chunks, buffer
    append_result("🎙️ 音声入力待機中...\n")

    while True:
        chunk = await asyncio.to_thread(record_queue.get)

        if has_started_speaking(chunk) and not speaking:
            append_result("🎤 話し始めを検出")
            speaking = True
            buffer = [chunk]
            silence_chunks = 0
        elif speaking:
            buffer.append(chunk)
            if is_silent(chunk):
                silence_chunks += 1
                if silence_chunks >= MAX_SILENCE_CHUNKS:
                    append_result("🛑 話し終わり → 文字起こし")
                    await asyncio.to_thread(process_audio, buffer, append_result)
                    speaking = False
                    buffer = []
            else:
                silence_chunks = 0


def main_gui(page: ft.Page):
    page.title = "リアルタイム音声認識"
    page.scroll = ft.ScrollMode.AUTO

    result_box = ft.Text(value="結果表示\n", selectable=True, expand=True)

    def append_result(text):
        result_box.value += text + "\n"
        page.update()

    def start_handler(_):
        append_result("🔄 モデルロード中...")
        model_id = "deepdml/faster-whisper-large-v3-turbo-ct2"
        model_ref["model"] = WhisperModel(model_id, device="cuda", compute_type="float16")
        append_result(f"✅ モデル: {model_id}")

        threading.Thread(target=record_stream, daemon=True).start()
        asyncio.run(main_loop(append_result))

    start_button = ft.ElevatedButton("音声認識開始", on_click=start_handler)

    page.add(result_box, start_button)


if __name__ == "__main__":
    ft.app(target=main_gui)