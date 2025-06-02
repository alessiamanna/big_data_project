import time
import base64
import requests
import asyncio

from pymongo import MongoClient
from pymongo.server_api import ServerApi

from concurrent.futures import ThreadPoolExecutor
from backend.llm_generator import generate_doctor_speech
from backend.text_to_speech import synthesize_text_to_wav

thread_number = 10
fastAPI_url = "http://localhost:8000/transcribe/" #ogni thread deve effettuare una post

uri = "mongodb+srv://alessia00m:Password1234@cluster0.7if8c41.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
client = MongoClient(uri, server_api=ServerApi('1'))
db = client["dati_clinici"]
collection = db["referti_ps"]

def thread_user(i):
    try:
        print(f"Thread {i} sta generando il referto")
        text = generate_doctor_speech()
        path_audio = asyncio.run(synthesize_text_to_wav(text)) #sintesi vocale

        print(f"Referto {i} generato, invio audio a /transcribe")

        with open(path_audio, "rb") as audio_file:
            files = {"file": ("audio.wav", audio_file, "audio/wav")}
            response = requests.post(fastAPI_url, files = files)

        if response.status_code == 200: #se la post è ok
            result = response.json()
            referto = result.get("structured_data", {})
            if referto and "errore" not in referto:
                collection.insert_one(referto)
                print(f"Referto {i} salvato")
        else:
            print(f"Thread {i}, errore http {response.status_code} - {response.text}")

    except Exception as e:
        print(f"Thread {i}: Errore durante la simulazione - {e}")

if __name__ == "__main__":
    print(f"Simulazione di {thread_number} thread")
    start = time.time()

    with ThreadPoolExecutor(max_workers = thread_number) as executor:
        executor.map(thread_user, range(1, thread_number+1))

    elapsed_time = time.time() - start

    print(f"Simulazione completata, tempo impiegato {elapsed_time}s")