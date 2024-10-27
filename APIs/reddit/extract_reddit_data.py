import json
import os
import re
from datetime import datetime, timezone
from collections import defaultdict
from helper.helper import companies_dict  # Importiere das Dictionary aus helper.py

# Eingabedatei und Ausgabeverzeichnis
input_file = r'C:\Users\noahv\Downloads\r_stocks_posts.jsonl'
output_dir = 'historical_data/'


# Hilfsfunktion zum Erstellen des Dateinamens
def generate_filename(subreddit, created_utc):
    date = datetime.fromtimestamp(created_utc, timezone.utc)
    year = date.strftime('%Y')
    month = date.strftime('%m')

    # Ordner für Jahr und Monat erstellen
    sub_dir = os.path.join(output_dir, year, month)
    os.makedirs(sub_dir, exist_ok=True)

    return os.path.join(sub_dir, f"reddit_{subreddit}_{date.strftime('%Y_%m_%d')}.json")


# Funktion zum Verarbeiten und Schreiben der Dateien
def process_reddit_data():
    # Datenstruktur für gesammelte Beiträge
    data_by_file = defaultdict(list)

    with open(input_file, 'r', encoding='utf-8') as file:
        for line in file:
            entry = json.loads(line.strip())

            # Eintragsinformationen extrahieren
            subreddit = entry.get("subreddit")
            title = entry.get("title", "").lower()
            selftext = entry.get("selftext", "").lower()
            post_id = entry.get("id")
            created_utc = entry.get("created_utc")

            # Prüfen, ob der Beitrag eine der Aktien erwähnt
            mentioned = False
            for company, ticker in companies_dict.items():
                # Erstellen von regulären Ausdrücken, um nur ganze Wörter zu finden
                company_pattern = re.compile(r'\b' + re.escape(company.lower()) + r'\b')
                ticker_pattern = re.compile(r'\b' + re.escape(ticker.lower()) + r'\b')

                if company_pattern.search(title) or company_pattern.search(selftext) or ticker_pattern.search(
                        title) or ticker_pattern.search(selftext):
                    mentioned = True
                    break

            if not mentioned:
                continue

            # Relevante Datenstruktur
            post_data = {
                "subreddit": subreddit,
                "title": entry.get("title"),
                "id": post_id
            }

            # Datei für den Beitrag bestimmen
            filename = generate_filename(subreddit, created_utc)
            data_by_file[filename].append(post_data)

    # In Dateien schreiben
    for filename, posts in data_by_file.items():
        with open(filename, 'w', encoding='utf-8') as output_file:
            json.dump(posts, output_file, ensure_ascii=False, indent=4)


# Hauptfunktion ausführen
if __name__ == "__main__":
    process_reddit_data()
