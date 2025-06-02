import json
from typing import Optional
from pydantic import BaseModel, Field, ValidationError
from langchain.output_parsers import PydanticOutputParser
from huggingface_hub import InferenceClient

#modello pydantic, tutti i campi sono opzionali
class RefertoClinico(BaseModel):
    nome_paziente: Optional[str]
    cognome_paziente: Optional[str]
    codice_fiscale: Optional[str]
    data_nascita: Optional[str]
    sesso: Optional[str]
    indirizzo: Optional[str]
    telefono: Optional[str]
    email: Optional[str]
    data_visita: Optional[str]
    luogo_visita: Optional[str]
    motivo_visita: Optional[str]
    anamnesi: Optional[str]
    esame_obiettivo: Optional[str]
    diagnosi: Optional[str]
    terapia: Optional[str]
    esami_strumentali: Optional[str]
    esami_laboratorio: Optional[str]
    allergie: Optional[str]
    farmaci_in_corso: Optional[str]
    note: Optional[str]

#funzione da richiamare nel main
def extract_json_from_transcription(transcription: str) -> dict:
    # Parser e istruzioni di formato
    parser = PydanticOutputParser(pydantic_object=RefertoClinico)
    format_instructions = parser.get_format_instructions()

    # Prompt da inviare al modello
    prompt = (
        f"{transcription.strip()}\n\n"
        "Sulla base delle informazioni cliniche precedenti, genera unicamente un oggetto JSON. Considera il contesto clinico, che siamo in una situazione di emergenza di pronto soccorso, quindi utilizza i termini medici/ospedalieri corretti e correggi eventuali errori grammaticali o di trascrizione, ricorda sempre che siamo in un contesto medico\n"
        "Se mancanti, Fai anche ipotesi sul sesso del paziente, sulla diagnosi e su eventuali esami strumentali e di laboratorio che il paziente dovrebbe effettuare.\n"
        "Non aggiungere alcun commento, codice markdown, testo introduttivo o di chiusura.\n"
        "Inizia direttamente con la parentesi graffa '{'.\n"
        "Formato desiderato:\n"
        f"{format_instructions}\n"
    )

    # Client API Hugging Face
    client = InferenceClient(
        model="google/gemma-2b-it",
        token="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"
    )

    try:
        completion = client.chat.completions.create(
            model="google/gemma-2b-it",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=512,
            temperature=0.3
        )
        output_raw = completion.choices[0].message.content.strip()

        try:
            # Parsing e validazione con Pydantic
            parsed = parser.parse(output_raw)
            return parsed.dict()
        except ValidationError as e:
            return {
                "errore": "Validazione fallita",
                "dettagli": str(e),
                "output_raw": output_raw
            }
        except Exception as e:
            return {
                "errore": "Parsing generico fallito",
                "dettagli": str(e),
                "output_raw": output_raw
            }

    except Exception as e:
        return {
            "errore": f"Errore nella chiamata API: {str(e)}"
        }
