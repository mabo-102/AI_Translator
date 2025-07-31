import os
import asyncio
import logging
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

# 音声パラメータ(デフォルト値)
SAMPLERATE = 16000
CHUNK_DURATION = 0.5
SILENT_THRESHOLD = 5
SPEECH_THRESHOLD = 50
MAX_SILENCE_CHUNKS = 4

CHUNK_SIZE = int(SAMPLERATE * CHUNK_DURATION)
CHANNELS = 1

params = {
    "samplerate": SAMPLERATE,
    "chunk_duration": CHUNK_DURATION,
    "silent_threshold": SILENT_THRESHOLD,
    "speech_threshold": SPEECH_THRESHOLD,
    "max_silence_chunks": MAX_SILENCE_CHUNKS
}

MODEL_ID = "deepdml/faster-whisper-large-v3-turbo-ct2"
model = WhisperModel(MODEL_ID, device="cuda", compute_type="float16")
logging.info(f"Loaded model: {MODEL_ID}")
model_ref = {"model": model}

record_queue = queue.Queue()
speaking = False
silence_chunks = 0
buffer = []
last_rms = 0

def is_silent(chunk):
    rms = np.sqrt(np.mean(chunk.astype(np.float32) ** 2))
    return rms < params["silent_threshold"]

def has_started_speaking(chunk):
    global last_rms
    rms = np.sqrt(np.mean(chunk.astype(np.float32) ** 2))
    triggered = rms > params["speech_threshold"] and last_rms < params["speech_threshold"]
    last_rms = rms
    logging.info(f"triggered rms: {triggered} => {last_rms}")
    return triggered

def transcribe_file(file_path, append_result):
    append_result(f"\U0001F4C2 ファイル選択: {file_path}")
    model = model_ref.get("model")
    if model is None:
        append_result("❌ モデルが読み込まれていません")
        return

    segments, _ = model.transcribe(file_path, language="ja")
    for seg in segments:
        append_result(f"[{seg.start:.1f}s → {seg.end:.1f}s] {seg.text.strip()}")

    append_result(f"🎉 ファイル文字起こし完了！")

def process_audio(chunks, append_result):
    logging.info("🔁 認識中...")
    audio_np = np.concatenate(chunks, axis=0)

    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        write(tmp.name, params["samplerate"], audio_np)
        tmp_path = tmp.name

    model = model_ref.get("model")
    if model is None:
        append_result("❌ モデルが読み込まれていません")
        return

    segments, _ = model.transcribe(tmp_path, language="ja", vad_filter=True)
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
        samplerate=params["samplerate"],
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
                if silence_chunks >= params["max_silence_chunks"]:
                    append_result("🛑 話し終わり → 文字起こし")
                    await asyncio.to_thread(process_audio, buffer, append_result)
                    speaking = False
                    buffer = []
            else:
                silence_chunks = 0

def main_gui(page: ft.Page):
    page.title = "AI多言語翻訳"
    page.scroll = ft.ScrollMode.AUTO

    def append_result(text):
        result_box.value += text + "\n"
        page.update()

    def start_handler(_):
        threading.Thread(target=record_stream, daemon=True).start()
        asyncio.run(main_loop(append_result))

    # 設定ダイアログの定義
    def settings_update(e):
        logging.info(f"params: {params}")
        params['samplerate'] = int(samplerate.value)
        params['chunk_duration'] = float(chunk_duration.value)
        params['silent_threshold'] = float(silent_threshold.value)
        params['speech_threshold'] = float(speech_threshold.value)
        params['max_silence_chunks'] = int(max_silence_chunks.value)
        page.update()
        logging.info(f"params updated: {params}")

    def default_settings(e):
        logging.info(f"params: {params}")
        params['samplerate'] = SAMPLERATE
        params['chunk_duration'] = CHUNK_DURATION
        params['silent_threshold'] = SILENT_THRESHOLD
        params['speech_threshold'] = SPEECH_THRESHOLD
        params['max_silence_chunks'] = MAX_SILENCE_CHUNKS

        samplerate.value = SAMPLERATE
        chunk_duration.value = CHUNK_DURATION
        silent_threshold.value = SILENT_THRESHOLD
        speech_threshold.value = SPEECH_THRESHOLD
        max_silence_chunks.value = MAX_SILENCE_CHUNKS
        page.update()
        logging.info(f"params default: {params}")

    samplerate = ft.TextField(label="サンプルレート", value=str(params["samplerate"]))
    chunk_duration = ft.TextField(label="チャンク時間(s)", value=str(params["chunk_duration"]))
    silent_threshold = ft.TextField(label="無音閾値", value=str(params["silent_threshold"]))
    speech_threshold = ft.TextField(label="話し始め閾値", value=str(params["speech_threshold"]))
    max_silence_chunks = ft.TextField(label="最大無音フレーム数", value=str(params["max_silence_chunks"]))
    settings = [samplerate, chunk_duration, silent_threshold, speech_threshold, max_silence_chunks]

    settings_dialog = ft.AlertDialog(
        modal=True,
        title=ft.Text("音声パラメータ設定"),
        content=ft.Column(settings, tight=True),
        actions=[
            ft.TextButton("保存", on_click=settings_update),
            ft.TextButton("初期値に戻す", on_click=default_settings),
            ft.TextButton("閉じる", on_click=lambda e: page.close(settings_dialog)),
        ],
        actions_alignment=ft.MainAxisAlignment.END,
        on_dismiss = lambda e: print(f"Modal dialog dismissed")
    )

    settings_button = ft.ElevatedButton(
        content=ft.Row([ft.Icon(name=ft.Icons.SETTINGS)]),
        on_click=lambda e: page.open(settings_dialog)
    )

    # UI
    def file_picker_result(e: ft.FilePickerResultEvent):
        if e.files:
            transcribe_file(e.files[0].path, append_result)

    pick_files_dialog = ft.FilePicker(on_result=file_picker_result)
    file_recognition = ft.Container(
        content=ft.Column([
            ft.Text("▶ 音声ファイルによる文字起こし", style="headlineSmall"),
            ft.Row([
                ft.ElevatedButton("ファイル選択", on_click=lambda _: pick_files_dialog.pick_files())
            ])
        ]),
        padding=10,
        bgcolor=ft.Colors.BLUE_50,
        border_radius=10
    )

    mic_recognition = ft.Container(
        content=ft.Column([
            ft.Text("▶ マイクによるリアルタイム音声認識", style="headlineSmall"),
            ft.Row([
                ft.ElevatedButton("マイク音声認識開始", on_click=start_handler)
            ])
        ]),
        padding=10,
        bgcolor=ft.Colors.GREEN_50,
        border_radius=10
    )

    result_box = ft.Text(value="結果表示", selectable=True, expand=True)

    # アプリ全体レイアウト
    header = ft.Row([
        ft.Text("音声認識アプリ", style="titleLarge"),
        settings_button
    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)

    layout = ft.Container(
        content=ft.Column([
            header,
            file_recognition,
            mic_recognition,
            result_box
        ], expand=True, spacing=20),
        padding=20
    )

    page.overlay.append(pick_files_dialog)
    page.add(layout)

if __name__ == "__main__":
    ft.app(target=main_gui)
