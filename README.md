# AI_Translator

version: 0.1.0 (ドラフト版)

## 音声でつながる！ローカルAI通訳アプリ開発入門（対話形式・KDP対応版）

### はじめに

**あなた（ITの専門家）**： 「こんにちは。今日は、ローカル環境で動く音声通訳アプリの作り方を一緒に学びましょう。」

**生徒（IT初心者）**： 「よろしくお願いします！オンラインに頼らずに動くアプリって、どんなメリットがあるんですか？」

**あなた**： 「通信コストがかからない、プライバシーが守られる、ネット接続が不安定でも動く――などがあります。これを機に、AI技術の基礎から実践まで体験してみましょう。」

---

## 目次

1. **イントロダクション** 〜学習ロードマップを対話で理解〜
2. **開発環境の準備** 〜ツール導入を会話形式で解説〜
3. **リアルタイム音声認識** 〜Whisper Live実践編〜
4. **ローカルLLMとの連携** 〜LM Studio APIを叩いてみよう〜
5. **音声で返答しよう（TTS）** 〜edge-ttsハンズオン〜
6. **GUI構築①** 〜Fletで見た目を作る〜
7. **録音制御と非同期処理** 〜UIと処理の連携〜
8. **多言語対応と翻訳モード** 〜動的切替を体験〜
9. **会話履歴の管理** 〜履歴表示・保存・再読込〜
10. **配布用実行ファイルの作成** 〜PyInstallerで公開準備〜

---

### 第1章：イントロダクション 〜学習ロードマップを対話で理解〜

**生徒**： 「まずは、この本の全体像を教えてください。」

**あなた**： 「10ステップで進みます。ステップ1で環境を整え、ステップ2〜4で音声→テキスト→AI→音声の基本パイプラインを作成。ステップ5以降でUIや多言語対応、履歴保存、最終的に配布用ファイル化まで学びます。」

**学習ポイント**

- 翻訳プロセスの全体像
- 各ステップの目的と到達目標

**ストーリー進行**

1. **背景説明**：「オンライン依存の課題」を例え話で紹介
2. **目標共有**：「完成形アプリで旅行先で即時通訳を体験する」ビジョン設定

---

### 第2章：開発環境の準備 〜ツール導入を会話形式で解説〜

**生徒**： 「PythonやGitは初めてです。何から始めればいい？」

**あなた**： 「まずPythonをインストールしましょう。公式サイトから3.10以上をダウンロードして、PATHを通すところからスタートです。」

**手順と対話**

1. **Python導入**：
   ```bash
   # Windows/macOS/Linux
   curl -O https://www.python.org/ftp/python/3.12.0/python-3.12.0-amd64.exe
   # Windowsの場合
   python-3.12.0-amd64.exe /quiet InstallAllUsers=1 PrependPath=1
   # バージョン確認\python
   python --version
   ```
2. **Git/GitHub設定**：
   ```bash
   # Gitインストール（Windows例）
   winget install --id Git.Git -e --source winget
   git config --global user.name "あなたの名前"
   git config --global user.email "you@example.com"
   ```
3. **VSCode推奨設定**：
   - 拡張機能: Python, Pylance, GitLens
   - settings.json に以下追加:
     ```json
     {
       "python.linting.flake8Enabled": true,
       "editor.formatOnSave": true
     }
     ```
4. **仮想環境作成**：
   ```bash
   # venv
   python -m venv venv
   source venv/bin/activate  # macOS/Linux
   venv\Scripts\activate     # Windows
   pip install --upgrade pip
   ```
5. **Whisper Liveインストール**：
   ```bash
   pip install git+https://github.com/pluja/whisper-live.git
   whisper-live --download-model small
   ```
6. **LM Studio導入**：公式サイトからインストーラを実行。
7. **edge-tts／playsound設定**：
   ```bash
   pip install edge-tts playsound
   ```
8. **Flet導入**：
   ```bash
   pip install flet
   ```

**ストーリー進行**

- 生徒のエラー発生 (`pip install` 失敗) → あなたが `python -m pip install --upgrade pip` を提案 → 解決

---

### 第3章：リアルタイム音声認識 〜Whisper Live実践編〜

**生徒**： 「マイクから音声を文字にするってどうやるの？」

**あなた**： 「コマンド一行です。`whisper-live --model base --language ja` で実行できます。」

**手順と対話**

1. **コマンド実行**：
   ```bash
   whisper-live --model base --language ja --device default
   ```
2. **サンプル入力**：
   - 生徒が「こんにちは、AIさん！」と言う→
   ```text
   > こんにちは、AIさん！
   > こんにちは AI さん  
   ```
3. **モデル変更**：
   ```bash
   whisper-live --model small --language ja
   ```
4. **GPU利用**：
   ```bash
   whisper-live --model base --language ja --device cuda
   ```
5. **トラブル対応**：
   - `ModuleNotFoundError: No module named 'pyaudio'` →
     ```bash
     pip install pipwin
     pipwin install pyaudio
     ```

**ストーリー進行**

- 生徒がtiny/small/baseを試し、速度と精度を比較して最適モデルを選択

---

### 第4章：ローカルLLMとの連携 〜LM Studio APIを叩いてみよう〜

**生徒**： 「文字起こししたテキストをどう翻訳するの？」

**あなた**： 「LM StudioのAPIを使います。PythonからHTTPリクエストを送るコードを書いてみましょう。」

**手順と対話**

1. **APIサーバー起動**：LM Studioアプリ内で「API Server」をONにし、ポートを`1234`に設定。
2. **curlテスト**：
   ```bash
   curl -X POST http://localhost:1234/v1/chat/completions \
     -H "Content-Type: application/json" \
     -d '{"model":"local-model","messages":[{"role":"system","content":"あなたは通訳者です。"},{"role":"user","content":"こんにちは"}]}'
   ```
3. **Python実装**：
   ```python
   import openai
   openai.api_base = "http://localhost:1234/v1"
   openai.api_key = ""

   def get_ai_response(prompt):
       resp = openai.ChatCompletion.create(
           model="local-model",
           messages=[
               {"role":"system","content":prompt},
               {"role":"user","content":"こんにちは"}
           ]
       )
       return resp.choices[0].message.content
   ```
4. **プロンプト調整**：
   ```python
   system_prompt = "あなたは日本語から英語へのプロの通訳者です。"
   ```
5. **エラー対応**：
   - `openai.error.APIConnectionError` → サーバーURL確認、ファイアウォール設定をチェック

**ストーリー進行**

- 生徒がレスポンスが長すぎると指摘 → `max_tokens=100` を追加 → 解決

---

### 第5章：音声で返答しよう（TTS） 〜edge-ttsハンズオン〜

**生徒**： 「翻訳結果を音声で返したいです。」

**あなた**： 「edge-ttsを使ってみましょう。非同期関数でMP3を生成し、自動再生します。」

**手順と対話**

1. **ライブラリ導入**：
   ```bash
   pip install edge-tts playsound
   ```
2. **基本コード**：
   ```python
   import asyncio
   import edge_tts
   import os

   async def speak(text, voice="ja-JP-NanamiNeural"):
       communicate = edge_tts.Communicate(text=text, voice=voice)
       await communicate.save("reply.mp3")
       os.system("start reply.mp3")  # Windows

   asyncio.run(speak("こんにちは、AIです。"))
   ```
3. **多言語テスト**：
   ```python
   asyncio.run(speak("Hello, how are you?", voice="en-US-AriaNeural"))
   ```
4. **非同期解説**：UIレスポンス維持のため、`await`の意味を説明
5. **エラー対応**：ファイルが再生できない場合、`playsound`使用例
   ```python
   from playsound import playsound
   playsound("reply.mp3")
   ```

**ストーリー進行**

- 生徒が日本語・英語の声を比較し、お気に入りを選定

---

### 第6章：GUI構築① 〜Fletで見た目を作る〜

**生徒**： 「見た目がないと使いづらそう…」

**あなた**： 「Fletでチャット風UIを作りましょう。DropDownとボタン、履歴表示の配置から解説します。」

**手順と対話**

1. **Page設定**：
   ```python
   import flet as ft

   def main(page: ft.Page):
       page.title = "AI通訳チャット"
       page.window_width = 600
       page.window_height = 800
   ```
2. **コンポーネント配置**：
   ```python
       pair_dropdown = ft.Dropdown(
           label="翻訳モード",
           options=[ft.dropdown.Option("ja->en", text="日本語→英語")],
           value="ja->en",
       )
       record_button = ft.ElevatedButton(text="話す")
       chat_history = ft.Column(expand=True, scroll=ft.ScrollMode.AUTO)
       page.add(ft.Row([pair_dropdown, record_button]), chat_history)
   ```
3. **サンプル動作**：
   ```python
   def on_click(e):
       chat_history.controls.append(ft.Text("あなた: こんにちは"))
       chat_history.controls.append(ft.Text("AI   : Hello"))
       page.update()
   record_button.on_click = on_click
   ```
4. **スタイリング**：padding指定例
   ```python
       page.padding = 10
       record_button.style = ft.ButtonStyle(padding=10)
   ```
5. **デバッグ手法**：画面上ログ出力
   ```python
       page.add(ft.Text(f"ログ: ボタンが押されました"))
   ```

**ストーリー進行**

- 生徒がUIの配置をいじり、表示が崩れた→padding調整で解決

---

### 第7章：録音制御と非同期処理 〜UIと処理の連携〜

**生徒**： 「録音して翻訳して…と一連の流れを組み合わせたいです。」

**あなた**： 「ここが本番です。sounddeviceで録音→whispercppで文字起こし→LM Studio呼出→edge-ttsで再生、を非同期でつなげます。」

**手順と対話**

1. **録音関数**：
   ```python
   import sounddevice as sd
   import numpy as np

   def record_audio(duration=3, fs=16000):
       rec = sd.rec(int(duration*fs), samplerate=fs, channels=1, dtype='int16')
       sd.wait()
       wav_path = "output.wav"
       from scipy.io.wavfile import write
       write(wav_path, fs, np.squeeze(rec))
       return wav_path
   ```
2. **文字起こし関数**：
   ```python
   import whispercpp

   def transcribe(wav_path):
       model = whispercpp.Whisper("models/ggml-small.bin")
       result = model.transcribe(wav_path)
       return result['text']
   ```
3. **AI呼び出し関数**：前章の `get_ai_response()` を使用
4. **非同期ハンドラ**：
   ```python
   import asyncio

   async def handle_click(e):
       wav = await asyncio.to_thread(record_audio)
       text = await asyncio.to_thread(transcribe, wav)
       reply = await asyncio.to_thread(get_ai_response, text)
       await speak(reply)
   record_button.on_click = lambda e: asyncio.create_task(handle_click(e))
   ```
5. **例外処理**：
   ```python
   try:
       wav = await asyncio.to_thread(record_audio)
   except Exception as ex:
       page.add(ft.Text(f"録音エラー: {ex}"))
   ```

**ストーリー進行**

- 生徒が処理時間の長さに驚き→ステータス表示を追加してUX改善

---

### 第8章：多言語対応と翻訳モード 〜動的切替を体験〜

**生徒**： 「日本語→英語だけじゃなく、他の言語ペアも使いたいです。」

**あなた**： 「言語マッピングを辞書で用意し、Dropdownで選択した値からプロンプトを自動生成しましょう。」

**手順と対話**

1. **言語マッピング辞書**：
   ```python
   languages = {"ja":"日本語","en":"英語","zh":"中国語"}
   lang_map = {
       code:{"whisper":code,"tts_voice":voice}
       for code, voice in zip(languages.keys(),
           ["ja-JP-NanamiNeural","en-US-AriaNeural","zh-CN-XiaoxiaoNeural"])
   }
   ```
2. **Dropdown更新**：動的生成
3. **プロンプトビルド**：
   ```python
   def build_system_prompt(src, dst):
       return f"あなたは{languages[src]}から{languages[dst]}へのプロの通訳者です。"
   ```
4. **テスト実行**：日→中、中→英など複数パターン実行
5. **文字化け対策**：
   ```python
   with open(wav_path, encoding='utf-8'):
       # 読み込み処理
   ```

**ストーリー進行**

- 生徒が祖母との中国語会話を想像し、洋々と喜ぶ

---

### 第9章：会話履歴の管理 〜履歴表示・保存・再読込〜

**生徒**： 「通訳ログを残しておきたいんですが…」

**あなた**： 「JSON形式で履歴を保存し、次回起動時に読み込めます。SnackBarで完了通知も出しましょう。」

**手順と対話**

1. **データ構造設計**：
   ```python
   history = []  # {'src','user','dst','ai'} のリスト
   ```
2. **履歴表示関数**：
   ```python
   def add_message(role, lang, text):
       prefix = "▶あなた" if role=='user' else "▶AI"
       chat_history.controls.append(ft.Text(f"{prefix}({lang}): {text}"))
       page.update()
   ```
3. **保存関数**：
   ```python
   import json
   def save_history(path="history.json"):
       with open(path,'w',encoding='utf-8') as f:
           json.dump(history, f, ensure_ascii=False, indent=2)
   ```
4. **読み込み関数**：
   ```python
   def load_history(path="history.json"):
       import os
       if not os.path.exists(path): return
       data = json.load(open(path, encoding='utf-8'))
       for item in data: add_message('user',item['src'],item['user'])
   ```
5. **UX向上**：
   ```python
   page.snack_bar = ft.SnackBar(ft.Text(f"保存完了: {path}"))
   page.snack_bar.open=True
   page.update()
   ```

**ストーリー進行**

- 生徒が複数セッションを保存→再読込で振り返り感激

---

### 第10章：配布用実行ファイルの作成 〜PyInstallerで公開準備〜

**生徒**： 「完成したら友達にも配りたいです！」

**あなた**： 「PyInstallerで.exe化すれば、Python環境がなくても実行できます。オプションを確認してビルドしましょう。」

**手順と対話**

1. **基本コマンド**：
   ```bash
   pip install pyinstaller
   pyinstaller --onefile main.py
   ```
2. **フォルダ形式 vs 単一ファイル**：
   ```bash
   # フォルダ形式
   pyinstaller --onefolder main.py
   # 単一ファイル
   pyinstaller --onefile main.py
   ```
3. **アイコン・データ同梱**：
   ```bash
   pyinstaller --onefile --windowed --icon=app.ico \
       --add-data "models;models" --add-data "history.json;." main.py
   ```
4. **デバッグオプション**：
   ```bash
   pyinstaller --onefile --clean --noconfirm main.py
   ```
5. **配布準備**：
   ```bash
   pip freeze > requirements.txt
   ```

**ストーリー進行**

- 生徒が.exeを他のPCで実行し、動作確認して歓喜

---

> **これで全章に具体的なコードやコマンドを追加しました。**

---

## 付録

### A. 各ツール公式サイト一覧

| ツール            | 公式サイト URL                                                                                        |
| -------------- | ------------------------------------------------------------------------------------------------ |
| Whisper Live   | [https://github.com/pluja/whisper-live](https://github.com/pluja/whisper-live)                   |
| faster-whisper | [https://github.com/guillaumekln/faster-whisper](https://github.com/guillaumekln/faster-whisper) |
| LM Studio      | [https://lmstudio.ai](https://lmstudio.ai)                                                       |
| edge-tts       | [https://github.com/rany2/edge-tts](https://github.com/rany2/edge-tts)                           |
| Flet           | [https://flet.dev](https://flet.dev)                                                             |
| PyInstaller    | [https://www.pyinstaller.org](https://www.pyinstaller.org)                                       |
| Git            | [https://git-scm.com](https://git-scm.com)                                                       |
| Python         | [https://www.python.org](https://www.python.org)                                                 |

### B. Python基礎リファレンス

#### 1. 構文

- **変数宣言**:
  ```python
  x = 10
  name = "Alice"
  ```
- **制御構文**:
  ```python
  if x > 5:
      print("大きいです")
  else:
      print("小さいです")

  for i in range(3):
      print(i)
  ```

#### 2. 関数

- **定義と呼び出し**:
  ```python
  def greet(name: str) -> str:
      return f"こんにちは、{name}さん！"

  message = greet("太郎")
  print(message)
  ```
- **デフォルト引数**:
  ```python
  def add(a: int, b: int = 5) -> int:
      return a + b

  print(add(3))    # 8
  print(add(3,2))  # 5
  ```

#### 3. クラス

- **定義とインスタンス化**:
  ```python
  class Person:
      def __init__(self, name: str, age: int):
          self.name = name
          self.age = age

      def say_hello(self) -> None:
          print(f"私は{self.name}、{self.age}歳です。")

  p = Person("花子", 20)
  p.say_hello()
  ```

#### 4. モジュールとパッケージ

- **モジュールインポート**:
  ```python
  import math
  from datetime import datetime

  print(math.pi)
  print(datetime.now())
  ```
- **自作パッケージ**:
  ```text
  myproject/
  ├─ mymodule.py
  └─ subpackage/
      └─ utils.py
  ```
  呼び出し例:
  ```python
  from myproject.mymodule import func
  from myproject.subpackage.utils import helper
  ```

