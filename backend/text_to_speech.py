import edge_tts
from datetime import datetime
import os
import random
from pydub import AudioSegment

voci = [
    "it-IT-ElsaNeural",
    "it-IT-IsabellaNeural",
    "it-IT-DiegoNeural"
]

async def synthesize_text_to_wav(text: str, output_dir: str = "audio") -> str:
    os.makedirs(output_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"discorso_{timestamp}.wav"
    file_path = os.path.join(output_dir, filename)

    voice = random.choice(voci)
    communicate = edge_tts.Communicate(text, voice=voice)
    await communicate.save(file_path)

    return file_path

def add_noise(voice_path, noise_path, output_path, noise_db=-20):
    voice = AudioSegment.from_file(voice_path)
    noise = AudioSegment.from_file(noise_path)

    if len(noise) < len(voice):
        loops = (len(voice) // len(noise)) + 1
        noise *= loops

    noise = noise - abs(noise_db)
    noise = noise[:len(voice)]

    combined = voice.overlay(noise)
    combined.export(output_path, format="wav")

