import os
import json
from transformers import GPT2Tokenizer

# Lade den GPT-2 Tokenizer
tokenizer = GPT2Tokenizer.from_pretrained("gpt2")

# Basisverzeichnis anpassen
base_directory = r'C:\Users\noahv\PycharmProjects\FinBot\APIs\reddit\output\2016'

# Tokenanzahl initialisieren
total_tokens = 0

# Durchlaufe alle Dateien im Verzeichnis und Unterverzeichnissen
for root, dirs, files in os.walk(base_directory):
    for file in files:
        print(total_tokens)
        if file.endswith(".jsonl"):
            file_path = os.path.join(root, file)

            # Datei öffnen und Zeile für Zeile lesen
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    # JSON-Zeile parsen
                    data = json.loads(line)

                    # Haupttextfelder für den Post
                    title = data.get("title", "")
                    selftext = data.get("selftext", "")

                    # Token für Titel und Text des Posts
                    title_tokens = tokenizer.encode(title)
                    selftext_tokens = tokenizer.encode(selftext)

                    # Tokens zur Gesamtanzahl hinzufügen
                    total_tokens += len(title_tokens) + len(selftext_tokens)

                    # Kommentare analysieren, falls vorhanden
                    comments = data.get("comments", [])
                    for comment in comments:
                        comment_body = comment.get("body", "")
                        comment_tokens = tokenizer.encode(comment_body)
                        total_tokens += len(comment_tokens)

                        # Prüfe auf verschachtelte Antworten
                        replies = comment.get("replies", [])
                        while replies:
                            reply = replies.pop(0)
                            reply_body = reply.get("body", "")
                            reply_tokens = tokenizer.encode(reply_body)
                            total_tokens += len(reply_tokens)

                            # Falls es weitere verschachtelte Antworten gibt, in die Liste hinzufügen
                            if "replies" in reply and reply["replies"]:
                                replies.extend(reply["replies"])

# Gesamte Tokenanzahl ausgeben
print("Gesamtanzahl der Tokens:", total_tokens)
