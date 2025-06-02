import random
from faker import Faker
from huggingface_hub import InferenceClient

fake = Faker("it_IT")
client = InferenceClient(model="google/gemma-2b-it", token="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")

SINTOMI = [
    "dolore toracico", "febbre alta", "cefalea", "dispnea", "vertigini", "nausea", "dolore addominale", "sincope", "frattura", "dolore al braccio", "vomito", "collasso", "tachicardia"
]

def generate_doctor_speech() -> str:
    #parametri fittizi generati con modulo faker
    nome = fake.first_name()
    cognome = fake.last_name()
    eta = random.randint(18, 90)
    sesso = random.choice(["M", "F"])
    sintomo = random.choice(SINTOMI)
    pressione = f"{random.randint(100, 180)}/{random.randint(40, 90)}"
    battito = random.randint(60, 140)
    saturazione = random.randint(80, 100)

    #prompt coi parametri generati 
    prompt = (
        f"Il paziente si chiama {nome} {cognome}, ha {eta} anni, sesso {sesso}. Se il sesso non ti sembra combaciare con il nome, cambialo, ma dillo per esteso. Ricavati anche la data e il luogo di nascita "
        f"È arrivato in pronto soccorso con {sintomo}. "
        f"Parametri vitali rilevati: pressione {pressione}, battito {battito}, saturazione {saturazione}%. "
        f"Scrivi un referto vocale completo in linguaggio naturale, come se il medico lo stesse dettando. "
        f"Includi sintomi, anamnesi, diagnosi, terapia ed esami richiesti, oltre che eventuali allergie ed intolleranze. "
        f"Lo stile deve essere discorsivo, umano, non un elenco di punti."
    )

    #chiamata all'llm, temperatura 0.9 per consentire maggiore creatività al modello
    response = client.chat.completions.create(
        model="google/gemma-2b-it",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=400,
        temperature=0.9
    )

    return response.choices[0].message.content.strip()
