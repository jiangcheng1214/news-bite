from utils.Utilities import get_clean_text
from typing import List
import clip
import torch


class OpenaiClipFeatureGenerator:
    _instance = None
    _device = None
    _model = None

    def __init__(self):
        assert OpenaiClipFeatureGenerator._instance is None, "Singleton class"
        self._device = "cuda" if torch.cuda.is_available() else "cpu"
        self._model, preprocess = clip.load('ViT-B/32', self._device)

    @staticmethod
    def get_instance():
        if OpenaiClipFeatureGenerator._instance is None:
            OpenaiClipFeatureGenerator._instance = OpenaiClipFeatureGenerator()
        return OpenaiClipFeatureGenerator._instance

    def get_similarity_score(self, text1: str, text2: str):
        text1_embedding = self.embedding_of(text1)
        text2_embedding = self.embedding_of(text2)
        similarity = torch.cosine_similarity(
            text1_embedding, text2_embedding).item()
        return similarity

    def embedding_of(self, text):
        clean_text = get_clean_text(text)
        text_input = clip.tokenize(clean_text).to(self._device)
        with torch.no_grad():
            text_features = self._model.encode_text(text_input)
        return text_features

    def find_best_match_and_score(self, candidates: List, target: str, maapping_func=lambda x: x):
        candidate_text_list = [get_clean_text(
            maapping_func(candidate)) for candidate in candidates]
        with torch.no_grad():
            target_text_feature = self.embedding_of(target)
            candidate_text_features = [self.embedding_of(
                candidate_text) for candidate_text in candidate_text_list]
        similarity_scores = [torch.cosine_similarity(
            target_text_feature, candidate_text_feature).item() for candidate_text_feature in candidate_text_features]
        most_similar_index = similarity_scores.index(
            max(similarity_scores))
        most_similar_item = candidates[most_similar_index]
        return most_similar_item, similarity_scores[most_similar_index]


if __name__ == "__main__":
    target_text = "youre pretty"
    # List of texts to compare against the target text
    text_list = ["you are a nice people", "you looks good",
                 "she likes you", "homework is hard"]

    generator = OpenaiClipFeatureGenerator.get_instance()
    print(generator.find_best_match_and_score(text_list, target_text))
