from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
import speech_recognition as sr
from gtts import gTTS
from pydub import AudioSegment
import uuid
import os
import shutil

app = FastAPI(title="Hindi + English STT + TTS")


@app.get("/", response_class=HTMLResponse)
async def home():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>STT + TTS</title>
        <style>
            body {
                font-family: Arial;
                background: linear-gradient(135deg, #667eea, #764ba2);
                color: white;
                text-align: center;
                padding-top: 40px;
            }
            .card {
                background: white;
                color: black;
                width: 420px;
                margin: 20px auto;
                padding: 20px;
                border-radius: 12px;
                box-shadow: 0px 4px 20px rgba(0,0,0,0.3);
            }
            input, button, select, textarea {
                margin: 8px;
                padding: 10px;
                width: 90%;
                border-radius: 6px;
                border: none;
            }
            button {
                background: #667eea;
                color: white;
                cursor: pointer;
            }
            button:hover {
                background: #5563c1;
            }
            textarea {
                height: 80px;
                resize: none;
            }
        </style>
    </head>
    <body>

        <h2>🎙 STT + TTS (Hindi + English)</h2>

        <!-- LANGUAGE -->
        <div class="card">
            <h3>🌍 Select Language</h3>
            <select id="language">
                <option value="hi-IN">Hindi</option>
                <option value="en-US">English</option>
            </select>
        </div>

        <!-- LIVE MIC CARD -->
        <div class="card">
            <h3>🎤 Live Mic (Real-Time Text)</h3>
            <button onclick="startListening()">Start Mic</button>
            <button onclick="stopListening()">Stop</button>
            <textarea id="liveText" placeholder="Live speech text..."></textarea>
        </div>

        <!-- FILE UPLOAD STT -->
        <div class="card">
            <h3>📂 File Upload → Text</h3>
            <form action="/stt" enctype="multipart/form-data" method="post">
                <input type="file" name="file" required>
                <input type="hidden" name="lang" id="stt_lang">
                <button type="submit" onclick="setSTTLanguage()">Convert</button>
            </form>
        </div>

        <!-- TTS -->
        <div class="card">
            <h3>🔊 Text → Speech</h3>
            <form action="/tts" method="post">
                <input type="text" name="text" placeholder="Type text..." required>
                <input type="hidden" name="lang" id="tts_lang">
                <button type="submit" onclick="setTTSLanguage()">Speak</button>
            </form>
        </div>

        <script>
            let recognition;

            function setSTTLanguage(){
                document.getElementById("stt_lang").value =
                    document.getElementById("language").value;
            }

            function setTTSLanguage(){
                document.getElementById("tts_lang").value =
                    document.getElementById("language").value;
            }

            function startListening(){
                recognition = new (window.SpeechRecognition || window.webkitSpeechRecognition)();
                recognition.lang = document.getElementById("language").value;
                recognition.continuous = true;

                recognition.onresult = function(event){
                    let text = "";
                    for(let i = 0; i < event.results.length; i++){
                        text += event.results[i][0].transcript;
                    }
                    document.getElementById("liveText").value = text;
                };

                recognition.start();
            }

            function stopListening(){
                if(recognition){
                    recognition.stop();
                }
            }
        </script>

    </body>
    </html>
    """


# ================================
# FILE STT
# ================================
@app.post("/stt")
async def speech_to_text(file: UploadFile = File(...), lang: str = Form(...)):

    try:
        uid = str(uuid.uuid4())
        input_file = f"{uid}_{file.filename}"
        wav_file = f"{uid}.wav"

        with open(input_file, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        audio = AudioSegment.from_file(input_file)
        audio = audio.set_channels(1)
        audio = audio.set_frame_rate(16000)
        audio.export(wav_file, format="wav")

        recognizer = sr.Recognizer()
        with sr.AudioFile(wav_file) as source:
            audio_data = recognizer.record(source)

        text = recognizer.recognize_google(audio_data, language=lang)

        os.remove(input_file)
        os.remove(wav_file)

        return {"recognized_text": text}

    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})


# ================================
# TTS
# ================================
@app.post("/tts")
async def text_to_speech(text: str = Form(...), lang: str = Form(...)):

    try:
        uid = str(uuid.uuid4())
        output_file = f"{uid}.mp3"

        tts_lang = "hi" if "hi" in lang else "en"

        tts = gTTS(text=text, lang=tts_lang)
        tts.save(output_file)

        return FileResponse(output_file, filename="speech.mp3")

    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})



if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, port=8000)
