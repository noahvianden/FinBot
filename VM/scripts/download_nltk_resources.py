import nltk
from transformers import AutoTokenizer, AutoModelForSequenceClassification; AutoTokenizer.from_pretrained('mrm8488/distilroberta-finetuned-financial-news-sentiment-analysis'); AutoModelForSequenceClassification.from_pretrained('mrm8488/distilroberta-finetuned-financial-news-sentiment-analysis')
from sentence_transformers import SentenceTransformer; SentenceTransformer('sentence-transformers/all-mpnet-base-v2')

# Lade die benötigten NLTK-Ressourcen herunter
nltk.download('stopwords')
nltk.download('wordnet')
nltk.download('omw-1.4')  # Für WordNet
