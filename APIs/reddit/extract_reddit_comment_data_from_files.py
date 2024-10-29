import json
import os
from collections import defaultdict

# Pfad zum Ordner mit den Kommentardaten
comments_folder = "historical_comment_data_raw"
structured_data = defaultdict(lambda: defaultdict(lambda: {"title": "", "selftext": "", "permalink": "", "created_utc": 0, "score": 0, "upvote_ratio": 0.0, "num_comments": 0, "comments": {}}))

# Zwischenspeicher für alle Kommentare
all_comments = defaultdict(lambda: defaultdict(dict))

# Alle JSONL-Dateien im Ordner durchlaufen
for filename in os.listdir(comments_folder):
    if filename.endswith(".jsonl"):
        with open(os.path.join(comments_folder, filename), 'r', encoding='utf-8') as f:
            for line in f:
                comment = json.loads(line.strip())

                subreddit = comment.get("subreddit", "unknown")
                post_id = comment.get("link_id", "unknown").split("_")[-1]  # Entferne das Präfix "t3_"
                comment_id = comment.get("id", "unknown")
                parent_id = comment.get("parent_id", "unknown").split("_")[-1]

                # Erstelle die Post-Struktur, falls sie noch nicht existiert
                if not structured_data[subreddit][post_id]["title"]:
                    structured_data[subreddit][post_id].update({
                        "title": "",  # Hier Titel des Posts einfügen
                        "selftext": "",  # Hier Text des Posts einfügen
                        "permalink": comment.get("permalink", ""),
                        "created_utc": comment.get("created_utc", 0),
                        "score": 0,  # Platzhalter für später
                        "upvote_ratio": 0.0,  # Platzhalter für später
                        "num_comments": 0,  # Platzhalter für später
                        "comments": {}
                    })

                # Kommentarstruktur erstellen
                comment_data = {
                    "body": comment.get("body", ""),
                    "score": comment.get("score", 0),
                    "created_utc": comment.get("created_utc", 0),
                    "replies": {}  # Platzhalter für mögliche Antworten
                }

                # Speichere Kommentar im Zwischenspeicher
                all_comments[subreddit][post_id][comment_id] = (comment_data, parent_id)

# Kommentare basierend auf parent_id verknüpfen
for subreddit, posts in all_comments.items():
    for post_id, comments in posts.items():
        for comment_id, (comment_data, parent_id) in comments.items():
            if parent_id == post_id:  # Top-Level-Kommentar
                structured_data[subreddit][post_id]["comments"][comment_id] = comment_data
            else:  # Antwort auf einen anderen Kommentar
                parent_comment = structured_data[subreddit][post_id]["comments"].get(parent_id)
                if parent_comment:
                    parent_comment["replies"][comment_id] = comment_data
                else:
                    # Falls der Parent-Kommentar nicht gefunden wird, füge ihn als Top-Level hinzu
                    structured_data[subreddit][post_id]["comments"][comment_id] = comment_data

# Struktur speichern oder weiter verarbeiten
with open("structured_reddit_comments.json", "w", encoding='utf-8') as f:
    json.dump(structured_data, f, indent=4)
