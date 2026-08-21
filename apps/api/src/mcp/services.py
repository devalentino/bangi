from typing import Annotated

from wireup import Inject, injectable


@injectable(lifetime='singleton')
class EmbeddingService:
    def __init__(self, embedding_model_path: Annotated[str, Inject(config='EMBEDDING_MODEL_PATH')]):
        self.embedding_model_path = embedding_model_path

    def compute(self, text: str) -> list[float]:
        from model2vec import StaticModel

        model = StaticModel.from_pretrained(self.embedding_model_path)
        return model.encode([text])[0].tolist()
