import os
import json
import time
from collections import defaultdict
from Trading_Bot.FinBot_TextMethods import TextProcessor
from Trading_Bot.FinBot_Relations import RelationAnalyzer
from concurrent.futures import ThreadPoolExecutor
from nltk.corpus import wordnet as wn
from nltk.corpus import stopwords


# Sicherstellen, dass NLTK-Ressourcen vollständig geladen sind
def preload_nltk_resources():
    try:
        wn.ensure_loaded()
        stopwords.words('english')
    except Exception as e:
        print(f"Fehler beim Vorladen von NLTK-Ressourcen: {e}")


class PostProcessor:
    def __init__(self):
        self.text_processor = TextProcessor()
        self.relation_analyzer = RelationAnalyzer()

    def filter_relevant_comments(self, comments, parent_body, parent_tickers):
        """
        Filtert relevante Kommentare rekursiv.
        """
        relevant_comments = []
        for comment in comments:
            comment_body = comment.get('body', '')
            comment_replies = comment.get('replies', [])
            comment_tickers = self.text_processor.find_tickers(comment_body)

            if not comment_tickers:
                if self.relation_analyzer.relates(parent_body, comment_body) and parent_tickers:
                    comment_tickers = parent_tickers
                else:
                    continue

            comment['replies'] = self.filter_relevant_comments(comment_replies, comment_body, comment_tickers)
            relevant_comments.append(comment)

        return relevant_comments

    def process_post(self, post):
        """
        Filtert relevante Inhalte in einem Post.
        """
        post_title = post.get('title', '')
        post_selftext = post.get('selftext', '')

        if post_selftext == '[deleted]':
            post_selftext = post_title

        post_tickers = self.text_processor.find_tickers(post_title) + self.text_processor.find_tickers(post_selftext)

        post['comments'] = self.filter_relevant_comments(post.get('comments', []), post_selftext, post_tickers)
        return post if post_tickers or post['comments'] else None


def process_file(input_path, output_path):
    """
    Verarbeitet eine JSONL-Datei und speichert nur relevante Daten.
    """
    try:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(input_path, 'r', encoding='utf-8') as infile, open(output_path, 'w', encoding='utf-8') as outfile:
            processor = PostProcessor()
            for line in infile:
                post = json.loads(line)
                filtered_post = processor.process_post(post)
                if filtered_post:
                    outfile.write(json.dumps(filtered_post) + '\n')
    except Exception as e:
        print(f"Fehler beim Verarbeiten der Datei {input_path}: {e}")


def process_directory(input_dir, output_dir, max_workers=4):
    """
    Verarbeitet alle JSONL-Dateien in einem Verzeichnis und speichert relevante Daten.
    """
    files_to_process = []

    for root, _, files in os.walk(input_dir):
        for file in files:
            if file.endswith('.jsonl'):
                rel_path = os.path.relpath(root, input_dir)
                input_file = os.path.join(root, file)
                output_file = os.path.join(output_dir, rel_path, file)
                files_to_process.append((input_file, output_file))

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        executor.map(lambda args: process_file(*args), files_to_process)


def main():
    input_directory = r'C:\Users\noahv\PycharmProjects\FinBot\Trading_Bot\Beispielposts'
    output_directory = r'C:\Users\noahv\PycharmProjects\FinBot\Trading_Bot\FilteredPosts'
    max_threads = 6

    preload_nltk_resources()

    if not os.path.exists(input_directory):
        print(f"Eingabeverzeichnis {input_directory} existiert nicht.")
        return

    process_directory(input_directory, output_directory, max_threads)


if __name__ == "__main__":
    main()
