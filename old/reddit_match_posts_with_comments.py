import os
import json
import logging
from datetime import datetime

# Konfiguration des Loggings
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler("processing.log"),
        logging.StreamHandler()
    ]
)

def process_posts(post_dir, comment_dir, output_dir, start_point=None):
    """
    Verarbeitet Posts und ihre zugehörigen Kommentare und speichert sie in .jsonl-Dateien.
    """
    logging.info("Starte die Verarbeitung der Posts.")
    # Durchläuft die Jahresordner
    years = sorted(os.listdir(post_dir))
    for year in years:
        year_path = os.path.join(post_dir, year)
        if not os.path.isdir(year_path):
            logging.debug(f"Überspringe {year_path}, da es kein Verzeichnis ist.")
            continue

        logging.info(f"Verarbeite Jahr: {year}")
        # Durchläuft die Monatsordner
        months = sorted(os.listdir(year_path))
        for month in months:
            month_path = os.path.join(year_path, month)
            if not os.path.isdir(month_path):
                logging.debug(f"Überspringe {month_path}, da es kein Verzeichnis ist.")
                continue

            logging.info(f"Verarbeite Monat: {month}")
            # Durchläuft die Tagesdateien
            day_files = sorted(os.listdir(month_path))
            for day_file in day_files:
                if not day_file.endswith('.jsonl'):
                    logging.debug(f"Überspringe {day_file}, da es keine .jsonl-Datei ist.")
                    continue

                day_file_path = os.path.join(month_path, day_file)
                subreddit = extract_subreddit(day_file)

                # Überprüft den Startpunkt
                if start_point:
                    file_date = datetime.strptime(f"{year}-{month}-{extract_day(day_file)}", "%Y-%m-%d")
                    if file_date < start_point:
                        logging.debug(f"Überspringe Datei {day_file_path}, da sie vor dem Startdatum liegt.")
                        continue

                logging.info(f"Verarbeite Datei: {day_file_path}")
                # Erstellt den Ausgabeordner
                output_path = os.path.join(output_dir, year, month, extract_day(day_file), subreddit)
                os.makedirs(output_path, exist_ok=True)

                # Verarbeitet die Posts
                with open(day_file_path, 'r', encoding='utf-8') as post_file:
                    for line_num, line in enumerate(post_file, 1):
                        try:
                            post = json.loads(line)
                            post_id = post.get('id')
                            if not post_id:
                                logging.warning(f"Zeile {line_num} in {day_file_path} hat keine 'id'. Überspringe.")
                                continue

                            # Bereitet die Post-Daten vor
                            post_data = {
                                'subreddit': post.get('subreddit'),
                                'title': post.get('title'),
                                'selftext': post.get('selftext'),
                                'id': post_id,
                                'created_utc': post.get('created_utc'),
                                'score': post.get('score'),
                                'upvote_ratio': post.get('upvote_ratio'),
                                'num_comments': post.get('num_comments'),
                            }

                            logging.debug(f"Verarbeite Post {post_id} im Subreddit {subreddit}.")

                            # Sammelt zugehörige Kommentare und verschachtelt sie
                            comments = collect_comments(comment_dir, subreddit, post_id)

                            logging.info(f"Gefundene Kommentare für Post {post_id}: {len(comments)}")

                            # Überprüft, ob Kommentare gefunden wurden
                            if comments:
                                nested_comments = nest_comments(comments, post_id)
                            else:
                                nested_comments = []

                            # Füge die Top-Kommentare hinzu
                            post_data['top_comments'] = nested_comments

                            # Speichert die Daten in einer .jsonl-Datei
                            output_file = os.path.join(output_path, f"{post_id}.jsonl")
                            with open(output_file, 'w', encoding='utf-8') as out_f:
                                json.dump(post_data, out_f)
                                out_f.write('\n')

                            logging.info(f"Post {post_id} wurde erfolgreich verarbeitet und gespeichert.")

                        except json.JSONDecodeError as e:
                            logging.error(f"JSONDecodeError in Datei {day_file_path}, Zeile {line_num}: {e}")
                            continue
                        except Exception as e:
                            logging.exception(f"Fehler beim Verarbeiten des Posts {post_id}: {e}")
                            continue

def collect_comments(comment_dir, subreddit, post_id):
    """
    Sammelt alle Kommentare zu einem bestimmten Post.
    """
    comments = []
    found_files = 0
    # Sucht nach relevanten Kommentar-Dateien
    for root, dirs, files in os.walk(comment_dir):
        for comment_file in files:
            if not comment_file.endswith('.json') and not comment_file.endswith('.jsonl'):
                continue
            if subreddit.lower() not in comment_file.lower():
                continue

            comment_file_path = os.path.join(root, comment_file)
            found_files += 1
            logging.debug(f"Durchsuche Kommentar-Datei: {comment_file_path}")
            with open(comment_file_path, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    try:
                        comment = json.loads(line)
                        # Überprüfen Sie das Format von link_id
                        link_id = comment.get('link_id')
                        if link_id is None:
                            logging.debug(f"Kommentar in Zeile {line_num} hat kein 'link_id'. Überspringe.")
                            continue
                        # Entferne Präfixe aus link_id
                        link_id_clean = link_id.replace('t3_', '').replace('t1_', '')

                        if link_id_clean == post_id:
                            # Extrahiere nur die benötigten Felder
                            comments.append({
                                'id': comment.get('id'),
                                'parent_id': comment.get('parent_id'),
                                'body': comment.get('body'),
                                'score': comment.get('score'),
                            })
                    except json.JSONDecodeError as e:
                        logging.error(f"JSONDecodeError in {comment_file}, Zeile {line_num}: {e}")
                        continue
                    except Exception as e:
                        logging.exception(f"Fehler beim Verarbeiten eines Kommentars in {comment_file}: {e}")
                        continue
    logging.info(f"Durchsuchte {found_files} Kommentar-Dateien für Post {post_id}.")
    return comments

def nest_comments(comments, post_id):
    """
    Verschachtelt Kommentare basierend auf parent_id und id.
    """
    logging.debug(f"Beginne mit der Verschachtelung von {len(comments)} Kommentaren für Post {post_id}.")
    comment_dict = {comment['id']: comment for comment in comments}
    nested_comments = []

    for comment in comments:
        parent_id = comment['parent_id']
        if parent_id.startswith('t1_'):
            parent_comment_id = parent_id[3:]
            parent_comment = comment_dict.get(parent_comment_id)
            if parent_comment:
                if 'replies' not in parent_comment:
                    parent_comment['replies'] = []
                parent_comment['replies'].append(comment)
                logging.debug(f"Kommentar {comment['id']} wurde zu replies von {parent_comment_id} hinzugefügt.")
            else:
                # Elternkommentar nicht gefunden; fügen wir es als Top-Level hinzu
                nested_comments.append(comment)
                logging.warning(f"Elternkommentar {parent_comment_id} nicht gefunden für Kommentar {comment['id']}.")
        elif parent_id.startswith('t3_') and parent_id[3:] == post_id:
            # Top-Level-Kommentar
            nested_comments.append(comment)
            logging.debug(f"Kommentar {comment['id']} ist ein Top-Level-Kommentar.")

    # Entferne die 'parent_id' und 'id' Felder aus der Ausgabe
    def clean_comment(comment):
        comment.pop('parent_id', None)
        comment.pop('id', None)
        if 'replies' in comment:
            for reply in comment['replies']:
                clean_comment(reply)

    for comment in nested_comments:
        clean_comment(comment)

    logging.info(f"Verschachtelung abgeschlossen für Post {post_id}.")
    return nested_comments

def extract_subreddit(filename):
    """
    Extrahiert den Subreddit-Namen aus dem Dateinamen.
    """
    parts = filename.split('_')
    if len(parts) >= 4:
        subreddit = parts[1]
        logging.debug(f"Extrahierter Subreddit aus Dateiname {filename}: {subreddit}")
        return subreddit
    else:
        logging.warning(f"Konnte Subreddit nicht aus Dateiname {filename} extrahieren.")
        return "unknown"

def extract_day(filename):
    """
    Extrahiert den Tag aus dem Dateinamen.
    """
    parts = filename.split('_')
    if len(parts) >= 4:
        day = parts[-1].split('.')[0]
        logging.debug(f"Extrahierter Tag aus Dateiname {filename}: {day}")
        return day
    else:
        logging.warning(f"Konnte Tag nicht aus Dateiname {filename} extrahieren.")
        return "unknown"

if __name__ == "__main__":
    post_directory = 'historical_post_data_clean'
    comment_directory = 'historical_comment_data_raw'
    output_directory = 'processed_data'

    # Optionaler Startpunkt (als datetime-Objekt)
    start_date = datetime(2024, 10, 28)

    process_posts(post_directory, comment_directory, output_directory, start_date)
