
import json
import os

def load_word_db(lang="it", game="articles"):
    # Trova il percorso del file partendo dalla cartella del progetto
    base_path = os.path.dirname(os.path.dirname(__file__))
    db_path = os.path.join(base_path, "data", "words_db.json")
    
    try:
        with open(db_path, "r", encoding="utf-8") as f:
            full_db = json.load(f)
        
        processed_words = []
        for concept_id, data in full_db.items():
            # Controlla se la lingua e il gioco esistono per questo concetto
            if lang in data and game in data[lang]:
                word_data = data[lang][game]
                processed_words.append({
                    "parola": word_data["parola"],
                    "corretta": word_data["corretta"],
                    "opts": word_data["opts"]
                })
        return processed_words
    except FileNotFoundError:
        print(f"Errore: File non trovato in {db_path}")
        return []
