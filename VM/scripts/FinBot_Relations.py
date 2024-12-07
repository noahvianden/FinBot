from sentence_transformers import SentenceTransformer, util
import numpy as np
import torch

class RelationAnalyzer:
    _shared_model = None  # Class variable to load model once

    def __init__(self):
        self.device = 'cuda' if torch.cuda.is_available() else 'cpu'

        if RelationAnalyzer._shared_model is None:
            print("Loading SentenceTransformer model...")
            RelationAnalyzer._shared_model = SentenceTransformer(
                'sentence-transformers/all-mpnet-base-v2', device=self.device
            )

        self.model = RelationAnalyzer._shared_model

    def get_sentence_embedding(self, text):
        with torch.no_grad():
            embedding = self.model.encode(text, convert_to_tensor=False).astype(np.float32)
        return embedding

    def relates(self, parent_body, child_body):
        embedding1 = self.get_sentence_embedding(parent_body)
        embedding2 = self.get_sentence_embedding(child_body)
        similarity = util.cos_sim(embedding1, embedding2).item()
        return similarity
