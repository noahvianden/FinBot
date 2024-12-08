import os
import json
import logging
import cProfile
import pstats
import io
from FinBot_TextMethods import TextProcessor
from FinBot_Relations import RelationAnalyzer
from nltk.corpus import wordnet as wn, stopwords
import torch

def configure_logging(log_file_path):
    logging.basicConfig(
        level=logging.WARNING,
        format='%(asctime)s [%(levelname)s] %(message)s',
        handlers=[
            logging.FileHandler(log_file_path, encoding='utf-8'),
            logging.StreamHandler()
        ]
    )

def preload_nltk_resources():
    try:
        wn.ensure_loaded()
        stopwords.words('english')
    except Exception as e:
        logging.exception(f"Fehler beim Vorladen von NLTK-Ressourcen: {e}")

class PostProcessor:
    def __init__(self):
        self.text_processor = TextProcessor()
        self.relation_analyzer = RelationAnalyzer()

    def process_comments(self, comments, parent_body, parent_tickers):
        processed_comments = []
        for comment in comments:
            comment_body = comment.get('body', '')
            comment_replies = comment.get('replies', [])
            try:
                comment_tickers = self.text_processor.find_tickers(comment_body)
            except Exception as e:
                comment_tickers = []

            if not comment_tickers:
                try:
                    relates_score = self.relation_analyzer.relates(parent_body, comment_body)
                except Exception as e:
                    relates_score = None
            else:
                relates_score = None

            comment['tickers'] = comment_tickers
            comment['relates_score'] = relates_score

            if comment_replies:
                comment['replies'] = self.process_comments(comment_replies, comment_body, comment_tickers)
            else:
                comment['replies'] = []

            processed_comments.append(comment)

        return processed_comments

    def process_post(self, post):
        post_id = post.get('id', 'Unbekannt')
        logging.warning(f"Verarbeite Post mit ID: {post_id}")
        post_title = post.get('title', '')
        post_selftext = post.get('selftext', '')

        if post_selftext == '[deleted]':
            post_selftext = post_title

        try:
            title_tickers = self.text_processor.find_tickers(post_title)
            selftext_tickers = self.text_processor.find_tickers(post_selftext)
            post_tickers = title_tickers + selftext_tickers
        except Exception:
            post_tickers = []

        post['tickers'] = post_tickers

        comments = post.get('comments', [])
        if comments:
            post['comments'] = self.process_comments(comments, post_selftext, post_tickers)
        else:
            post['comments'] = []

        return post

def read_jsonl_file(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    yield json.loads(line)
                except json.JSONDecodeError:
                    continue
    except Exception as e:
        logging.exception(f"Fehler beim Lesen der Datei {file_path}: {e}")

def process_file(input_path, output_path, progress_file):
    processor = PostProcessor()
    processed_ids = set()

    if os.path.exists(progress_file):
        try:
            with open(progress_file, 'r', encoding='utf-8') as pf:
                processed_ids = set(json.load(pf))
            logging.info(f"Fortschritt aus {progress_file} geladen. Bereits verarbeitet: {len(processed_ids)} Posts.")
        except Exception as e:
            logging.exception(f"Fehler beim Laden des Fortschritts aus {progress_file}: {e}")

    logging.warning(f"Beginne mit der Verarbeitung der Datei: {input_path}")

    with open(output_path, 'a', encoding='utf-8') as outfile:
        for post in read_jsonl_file(input_path):
            if post.get('num_comments') > 250:
                print("überschpringen")
                continue
            post_id = post.get('id')
            if post_id in processed_ids:
                continue

            processed_post = processor.process_post(post)
            outfile.write(json.dumps(processed_post) + '\n')
            processed_ids.add(post_id)

            # Fortschritt nicht unbedingt nach jedem Post speichern, ggf. nur gelegentlich
            try:
                with open(progress_file, 'w', encoding='utf-8') as pf:
                    json.dump(list(processed_ids), pf)
            except Exception as e:
                logging.exception(f"Fehler beim Speichern des Fortschritts in {progress_file}: {e}")

def process_directory(input_dir, output_dir, progress_dir):
    files_to_process = []
    for root, _, files in os.walk(input_dir):
        for file in files:
            if file.endswith('.jsonl'):
                rel_path = os.path.relpath(root, input_dir)
                input_file = os.path.join(root, file)
                output_file = os.path.join(output_dir, rel_path, file)
                progress_file = os.path.join(progress_dir, rel_path, file + '.progress.json')
                os.makedirs(os.path.dirname(output_file), exist_ok=True)
                os.makedirs(os.path.dirname(progress_file), exist_ok=True)
                files_to_process.append((input_file, output_file, progress_file))

    logging.info(f"Gesamtanzahl der zu verarbeitenden Dateien: {len(files_to_process)}")
    if not files_to_process:
        logging.warning("Keine '.jsonl'-Dateien gefunden zum Verarbeiten.")
        return

    for input_file, output_file, progress_file in files_to_process:
        process_file(input_file, output_file, progress_file)

def main():
    preload_nltk_resources()
    for count in range(100, 251, 10):
        input_directory = f'../VM_Projects_Copy/{count}/input_data'
        output_directory = f'../VM_Projects_Copy/{count}/output_data'
        progress_directory = f'../VM_Projects_Copy/{count}/progress_data'

        log_file_path = os.path.join(progress_directory, "processing.log")
        configure_logging(log_file_path)

        logging.info(f"Starte die Verarbeitung für Projekt {count}.")
        print('cuda' if torch.cuda.is_available() else 'cpu')
        process_directory(input_directory, output_directory, progress_directory)

if __name__ == "__main__":
    main()

