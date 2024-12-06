from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch

class SentimentAnalyzer:
    def __init__(self):
        self.tokenizer = AutoTokenizer.from_pretrained('mrm8488/distilroberta-finetuned-financial-news-sentiment-analysis')
        self.model = AutoModelForSequenceClassification.from_pretrained('mrm8488/distilroberta-finetuned-financial-news-sentiment-analysis')
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.model.to(self.device)
        self.sentiment_cache = {}

    def analyze_sentiment_batch(self, texts):
        tokens = self.tokenizer(texts, return_tensors='pt', truncation=True, padding=True, max_length=512).to(self.device)
        with torch.no_grad():
            outputs = self.model(**tokens)
        probabilities = torch.softmax(outputs.logits, dim=1).cpu().numpy()
        return probabilities[:, 2] - probabilities[:, 0]  # Positivität - Negativität

    def analyze_sentiment(self, text):
        if text in self.sentiment_cache:
            return self.sentiment_cache[text]
        score = self.analyze_sentiment_batch([text])[0]
        self.sentiment_cache[text] = score
        return score
