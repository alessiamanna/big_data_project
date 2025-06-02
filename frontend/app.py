import streamlit as st
import requests
import base64
import sounddevice as sd
import scipy.io.wavfile
import io

from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi

#connessione a mongoDB
uri = "mongodb+srv://alessia00m:Password1234@cluster0.7if8c41.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"

#creo nuovo client e mi collego con la connection string 
client = MongoClient(uri, server_api=ServerApi('1'))

#conferma che la connessione sia avvenuta correttamente
try:
    client.admin.command('ping')
    print("Pinged your deployment. You successfully connected to MongoDB!")
except Exception as e:
    print(e)

db = client["dati_clinici"]
collection = db["referti_ps"]

#Page Configuration
st.set_page_config(
    page_title="Whisper Audio Transcriber",
    page_icon="🎧",
    layout="centered",
)

#Custom CSS Styling
st.markdown("""
    <style>
    .stApp {
        background-color: #1c1c1c;
        color: white;
    }
    .main, .block-container {
        background-color: #2e2e2e;
        color: white;
    }
    h1, h2, h3, h4, h5, h6, p, label, .stRadio > div, .stCheckbox > div, .stSlider > div, .stFileUploader > div {
        color: white !important;
    }
    .stRadio > label, .stCheckbox > label, .stSlider > label, .stFileUploader > label {
        color: white !important;
    }
    .st-bw {
        color: white !important;
    }
    </style>
""", unsafe_allow_html=True)

#Title and Description
st.title("Voice2Text")
st.markdown("AI-Powered Speech-to-Store&View Clinical Documentation")

#Live Mic Recording
record_option = st.checkbox("Record with Microphone")
uploaded_file = None

if record_option:
    duration = st.slider("Duration (seconds)", 1, 10, 5)
    if st.button("Record"):
        st.info("Recording...")
        fs = 44100
        recording = sd.rec(int(duration * fs), samplerate=fs, channels=1)
        sd.wait()

        # Save recording to BytesIO
        wav_io = io.BytesIO()
        scipy.io.wavfile.write(wav_io, fs, recording)
        wav_io.seek(0)
        uploaded_file = wav_io

        st.audio(wav_io, format="audio/wav")
else:
    uploaded_file = st.file_uploader("Choose your audio file", type=["mp3", "wav", "m4a", "ogg", "opus"])

#Transcription Button
if uploaded_file:
    if st.button("Transcribe"):
        with st.spinner("Transcribing..."):
            try:
                files = {
                    "file": (
                        "recording.wav",  # filename
                        uploaded_file.read() if not record_option else uploaded_file.getvalue(),
                        "audio/wav")
                }
                response = requests.post("http://localhost:8000/transcribe/", files=files) #post per comunicare col backend

                if response.status_code == 200:
                    data = response.json()
                    transcription = data.get("transcription", "")
                    language = data.get("language", "Unknown")
                    st.session_state["structured_data"] = data.get("structured_data", {})
                    elapsed_time = data.get("elapsed_time_seconds", None)
                    st.success("Transcription successful")
                    st.subheader("Here's what the doctor said:")
                    st.write(transcription)
                    st.markdown(f"**Language Detected:** `{language}`")
                    # --- Download Transcription ---
                    b64 = base64.b64encode(transcription.encode()).decode()
                    href = f'<a href="data:file/txt;base64,{b64}" download="transcription.txt">Download transcription</a>'
                    st.markdown(href, unsafe_allow_html=True)


                else:
                    st.error(f"Server error: {response.text}")
            except Exception as e:
                st.error(f"Something went wrong: {e}")

if st.button("Genera Referto Sintetico con Audio"):
    with st.spinner("Generazione e trascrizione in corso..."):
        response = requests.post("http://localhost:8000/generate_synthetic/")

        try:
            data = response.json()
        except Exception as e:
            st.error(f"Errore nel parsing JSON dal backend: {e}")
            st.text(response.text)
            st.stop()

        if "errore" in data:
            st.error(f"Errore dal backend: {data['errore']}")
            st.stop()

        st.success("Referto generato!")
        #audio generato con edge-tts
        audio_data = base64.b64decode(data["audio_base64"])
        st.audio(audio_data, format="audio/wav")

        st.subheader("Trascrizione del testo:")
        st.write(data["transcription"])

        st.subheader("Parsing JSON:")
        st.json(data["structured_data"])

        st.session_state["structured_data"] = data["structured_data"]

        
if "structured_data" in st.session_state:
    st.subheader("JSON estratto dalla trascrizione: ")
    st.json(st.session_state["structured_data"])

    if st.button("Salva sul database"):            
        structured_data = st.session_state.get("structured_data", {})
        if structured_data and "errore" not in structured_data:
            result = collection.insert_one(structured_data)
            st.success(f"Referto salvato! ID: {str(result.inserted_id)}")
        else:
            st.error("Referto non valido o mancante, non salvato.")
