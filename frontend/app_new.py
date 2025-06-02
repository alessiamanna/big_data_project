import streamlit as st
import requests
import base64
from pymongo import MongoClient
from pymongo.server_api import ServerApi

# MongoDB connection
uri = "mongodb+srv://alessia00m:Password1234@cluster0.7if8c41.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
client = MongoClient(uri, server_api=ServerApi('1'))
db = client["dati_clinici"]
collection = db["referti_ps"]

st.set_page_config(page_title="Voice2Care", layout="wide")
st.sidebar.title("Voice2Care Dashboard")
page = st.sidebar.radio("Navigazione", ["Home", "Nuovo Referto", "Visualizza Referti"])

if page == "Home":
    st.title("Voice2Care 🩺")
    st.markdown("""
    Sistema AI-Powered per la generazione, trascrizione, modifica e archiviazione di referti clinici
    tramite registrazioni vocali o generazione automatica.
    """)

elif page == "Nuovo Referto":
    st.header("🎙️ Nuovo Referto: Generazione o Trascrizione")

    # Upload o generazione
    option = st.radio("Modalità di inserimento", ["Carica Audio", "Genera Referto Sintetico"])

    if option == "Carica Audio":
        uploaded_file = st.file_uploader("Carica un file audio", type=["wav", "mp3", "m4a"])
        if uploaded_file and st.button("Trascrivi Audio"):
            with st.spinner("Trascrizione in corso..."):
                files = {"file": ("audio.wav", uploaded_file.read(), "audio/wav")}
                response = requests.post("http://localhost:8000/transcribe/", files=files)
                if response.status_code == 200:
                    data = response.json()
                    st.session_state["structured_data"] = data["structured_data"]
                    st.success("Trascrizione completata!")
                else:
                    st.error("Errore nella trascrizione.")

    elif option == "Genera Referto Sintetico":
        if st.button("Genera Referto Automatico"):
            with st.spinner("Generazione e trascrizione..."):
                response = requests.post("http://localhost:8000/generate_synthetic/")
                if response.status_code == 200:
                    data = response.json()
                    st.session_state["structured_data"] = data["structured_data"]
                    st.audio(base64.b64decode(data["audio_base64"]), format="audio/wav")
                    st.success("Referto generato con successo!")
                else:
                    st.error("Errore nella generazione del referto.")

    if "structured_data" in st.session_state:
        st.subheader("📝 Modifica Referto Estratto")
        d = st.session_state["structured_data"]

        col1, col2 = st.columns(2)
        with col1:
            nome = st.text_input("Nome Paziente", value=d.get("nome_paziente", ""))
            cf = st.text_input("Codice Fiscale", value=d.get("codice_fiscale", ""))
            sesso = st.selectbox("Sesso", ["M", "F"], index=0 if d.get("sesso", "M") == "M" else 1)
            data_nascita = st.text_input("Data di Nascita", value=d.get("data_nascita", ""))
        with col2:
            cognome = st.text_input("Cognome Paziente", value=d.get("cognome_paziente", ""))
            telefono = st.text_input("Telefono", value=d.get("telefono", ""))
            email = st.text_input("Email", value=d.get("email", ""))
            indirizzo = st.text_input("Indirizzo", value=d.get("indirizzo", ""))

        st.markdown("---")
        motivo = st.text_area("Motivo Visita", value=d.get("motivo_visita", ""))
        anamnesi = st.text_area("Anamnesi", value=d.get("anamnesi", ""))
        esame = st.text_area("Esame Obiettivo", value=d.get("esame_obiettivo", ""))
        diagnosi = st.text_area("Diagnosi", value=d.get("diagnosi", ""))
        terapia = st.text_area("Terapia", value=d.get("terapia", ""))
        esami_strum = st.text_area("Esami Strumentali", value=d.get("esami_strumentali", ""))
        esami_lab = st.text_area("Esami di Laboratorio", value=d.get("esami_laboratorio", ""))
        allergie = st.text_area("Allergie", value=d.get("allergie", ""))
        farmaci = st.text_area("Farmaci in corso", value=d.get("farmaci_in_corso", ""))
        note = st.text_area("Note aggiuntive", value=d.get("note", ""))

        final_data = {
            "nome_paziente": nome,
            "cognome_paziente": cognome,
            "codice_fiscale": cf,
            "data_nascita": data_nascita,
            "sesso": sesso,
            "telefono": telefono,
            "email": email,
            "indirizzo": indirizzo,
            "motivo_visita": motivo,
            "anamnesi": anamnesi,
            "esame_obiettivo": esame,
            "diagnosi": diagnosi,
            "terapia": terapia,
            "esami_strumentali": esami_strum,
            "esami_laboratorio": esami_lab,
            "allergie": allergie,
            "farmaci_in_corso": farmaci,
            "note": note
        }

        if st.button("💾 Salva nel Database"):
            try:
                result = collection.insert_one(final_data)
                st.success(f"Referto salvato con ID: {result.inserted_id}")
            except Exception as e:
                st.error(f"Errore salvataggio: {e}")

elif page == "Visualizza Referti":
    st.header("📂 Referti Salvati")
    results = list(collection.find().sort("_id", -1).limit(10))
    if results:
        for doc in results:
            with st.expander(f"{doc.get('nome_paziente', '')} {doc.get('cognome_paziente', '')} - {doc.get('data_visita', '')}"):
                for k, v in doc.items():
                    if k != "_id":
                        st.markdown(f"**{k.replace('_', ' ').capitalize()}**: {v}")
    else:
        st.info("Nessun referto trovato nel database.")
