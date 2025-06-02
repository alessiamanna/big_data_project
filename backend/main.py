from fastapi import FastAPI, UploadFile, File
from faster_whisper import WhisperModel
import whisper
import tempfile
import shutil
import os
import time
import torch
import traceback
from backend.llm_parser import extract_json_from_transcription
from backend.llm_generator import generate_doctor_speech
from backend.text_to_speech import synthesize_text_to_wav, add_noise
import base64

#path assoluto rispetto al file main.py
BASE_DIR = os.path.dirname(__file__)
path_noise = os.path.join(BASE_DIR, "audio", "noise.wav")

#se cuda è disponibile usa la gpu altrimenti usa la cpu
device = "cuda" if torch.cuda.is_available() else "cpu"

#se uso la gpu, compute type dev'essere float16 altrimenti int8
compute_type = "float16" if device == "cuda" else "int8"

#carico il modello di faster whisper, medium altrimenti la vram satura
model = WhisperModel("medium", device = device, compute_type = compute_type)

app = FastAPI()

print("🔍 Verifica CUDA...")
print("CUDA disponibile:", torch.cuda.is_available())
if torch.cuda.is_available():
    print("Dispositivo:", torch.cuda.get_device_name(0))
else:
    print("⚠️ CUDA non disponibile. Installa torch con supporto CUDA 12.1.")



@app.post("/transcribe/")
async def transcribe_audio(file: UploadFile = File(...)):
    # Save the uploaded file to a temporary location
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_audio_file:
        shutil.copyfileobj(file.file, temp_audio_file)
        temp_audio_path = temp_audio_file.name

    try:
        start_time = time.time()
        # Transcribe using FasterWhisper
        segments, info = model.transcribe(temp_audio_path)

        # Converte in lista per forzare la valutazione del generatore
        segment_list = list(segments)

        # Accede direttamente alla chiave `text` senza passare per `segment.text`
        texts = [s.__dict__["text"] for s in segment_list]

        transcription = "".join(texts)

        #qui estraggo il json dalla trascrizione
        structured_data = extract_json_from_transcription(transcription)

        end_time = time.time() 
        elapsed_time = end_time - start_time
        print("tempo impiegato per la trascrizione: ", elapsed_time)
        print("trascrizione", transcription)
        print(structured_data,"\n")
        
        return {
            "transcription": transcription.strip(),
            "language": info.language,
            "structured_data":structured_data
        }
    finally:
        os.remove(temp_audio_path)

import traceback

@app.post("/generate_synthetic/")
async def generate_synthetic():
    try:
        testo_originale = generate_doctor_speech()
        print(testo_originale)
        path_audio = await synthesize_text_to_wav(testo_originale)

        add_noise(path_audio, path_noise, path_audio, noise_db=-2)

        segments, info = model.transcribe(path_audio)
        segment_list = list(segments)
        testo_trascritto = "".join([s.__dict__["text"] for s in segment_list])

        structured_data = extract_json_from_transcription(testo_trascritto)

        with open(path_audio, "rb") as audio_file:
            audio_bytes = audio_file.read()
        audio_b64 = base64.b64encode(audio_bytes).decode("utf-8")

        return {
            "text_original": testo_originale,
            "transcription": testo_trascritto,
            "structured_data": structured_data,
            "audio_base64": audio_b64
        }

    except Exception as e:
        traceback.print_exc()  #stampa eventuali errori sul terminale
        return {"errore": str(e)}
