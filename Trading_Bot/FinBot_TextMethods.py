from nltk.stem import WordNetLemmatizer
from nltk.corpus import stopwords
import re
from APIs.helper.ticker_and_indicator import companies_dict, market_indicators

import nltk

# Laden der erforderlichen Daten
try:
    nltk.download('stopwords')
    nltk.download('wordnet')
    nltk.download('omw-1.4')  # Optional, falls für WordNet benötigt
except Exception as e:
    print(f"Fehler beim Herunterladen der NLTK-Daten: {e}")


class TextProcessor:
    def __init__(self):
        self.lemmatizer = WordNetLemmatizer()
        self.stopwords = set(stopwords.words('english'))
        self.tickers = set(map(str.lower, list(companies_dict.keys()) + list(companies_dict.values()) + market_indicators))
        self.ticker_to_name = {v.lower(): k.lower() for k, v in companies_dict.items()}
        self.name_to_ticker = {k.lower(): v.lower() for k, v in companies_dict.items()}

    def clean_text(self, text):
        text = text.lower()
        text = re.sub(r'[^a-zäöüß\s]', '', text)
        words = text.split()
        words = [w for w in words if w not in self.stopwords]
        words = [self.lemmatizer.lemmatize(w) for w in words]
        return ' '.join(words)

    def find_tickers(self, text):
        tokens = re.findall(r'\b\w+\b', text.lower())
        matches = set(token for token in tokens if token in self.tickers)
        return list(map(self.map_to_primary_ticker, matches))

    def map_to_primary_ticker(self, ticker):
        ticker = ticker.lower()
        if ticker in self.ticker_to_name:
            return ticker
        elif ticker in self.name_to_ticker:
            return self.name_to_ticker[ticker]
        return ticker
