from sentence_transformers import SentenceTransformer, util
from FinBot_TextMethods import TextProcessor
import os
import sqlite3
import threading
import atexit
import numpy as np

class RelationAnalyzer:
    def __init__(self, cache_size=100000, cache_path="embedding_cache4.db"):
        self.model = SentenceTransformer('sentence-transformers/all-mpnet-base-v2')
        self.cache_path = cache_path
        self.cache_size = cache_size
        self.text_processor = TextProcessor()
        self.cache_lock = threading.Lock()
        self.dirty = False

        # Initialisiere die SQLite-Datenbank
        self.conn = sqlite3.connect(self.cache_path, check_same_thread=False)
        self._initialize_db()

        atexit.register(self._close_db)

    def _initialize_db(self):
        with self.conn:
            self.conn.execute('''
                CREATE TABLE IF NOT EXISTS embeddings (
                    text TEXT PRIMARY KEY,
                    embedding BLOB
                )
            ''')
            self.conn.execute('''
                CREATE TABLE IF NOT EXISTS metadata (
                    key TEXT PRIMARY KEY,
                    value INTEGER
                )
            ''')
            # Initialize cache size if not set
            cursor = self.conn.execute("SELECT value FROM metadata WHERE key='cache_size'")
            row = cursor.fetchone()
            if not row:
                self.conn.execute("INSERT INTO metadata (key, value) VALUES (?, ?)", ('cache_size', self.cache_size))

    def _close_db(self):
        self.conn.close()

    def get_sentence_embedding(self, text):
        # Zuerst versuchen, das Embedding aus der Datenbank abzurufen
        cursor = self.conn.execute("SELECT embedding FROM embeddings WHERE text=?", (text,))
        row = cursor.fetchone()
        if row:
            embedding = np.frombuffer(row[0], dtype=np.float32)
            return embedding

        # Wenn nicht gefunden, bereinigen und kodieren
        clean_text = self.text_processor.clean_text(text)
        embedding = self.model.encode(clean_text, convert_to_tensor=False).astype(np.float32)

        # Speichern des Embeddings in der Datenbank
        with self.cache_lock:
            self.conn.execute(
                "INSERT OR REPLACE INTO embeddings (text, embedding) VALUES (?, ?)",
                (text, embedding.tobytes())
            )
            self.conn.commit()
            self.dirty = True
            self._enforce_cache_size()

        return embedding

    def _enforce_cache_size(self):
        # Überprüfen und Begrenzen der Cache-Größe
        cursor = self.conn.execute("SELECT COUNT(*) FROM embeddings")
        count = cursor.fetchone()[0]
        if count > self.cache_size:
            # Lösche ältere Einträge (hier einfach zufällig, für LRU müsste ein zusätzliches Feld benötigt werden)
            to_delete = count - self.cache_size
            self.conn.execute("DELETE FROM embeddings WHERE rowid IN (SELECT rowid FROM embeddings LIMIT ?)", (to_delete,))
            self.conn.commit()

    def relates(self, parent_body, child_body):
        embedding1 = self.get_sentence_embedding(parent_body)
        embedding2 = self.get_sentence_embedding(child_body)
        similarity = util.cos_sim(embedding1, embedding2).item()
        return similarity

    def save_cache(self):
        """Manuelles Speichern des Caches, hier nicht notwendig bei SQLite."""
        pass

# Beispiel für die Nutzung
if __name__ == "__main__":
    analyzer = RelationAnalyzer()

    # Beispieltexte
    text1 = "Dies ist ein Beispielsatz."
    text2 = "Dies ist ein anderer Satz für den Vergleich."

    similarity = analyzer.relates(text1, text2)
    print(f"Ähnlichkeit: {similarity}")
