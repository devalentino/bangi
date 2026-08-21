from typing import Annotated

from peewee import fn
from wireup import Inject, injectable

from src.core.utils import utcnow
from src.mcp.entities import AgentNote


@injectable(lifetime='singleton')
class EmbeddingService:
    def __init__(self, embedding_model_path: Annotated[str, Inject(config='EMBEDDING_MODEL_PATH')]):
        self.embedding_model_path = embedding_model_path

    def compute(self, text: str) -> list[float]:
        from model2vec import StaticModel

        model = StaticModel.from_pretrained(self.embedding_model_path)
        return model.encode([text])[0].tolist()


@injectable
class AgentNoteService:
    def upsert(self, session_id, note_text, embedding):
        (
            AgentNote.insert(session_id=session_id, note_text=note_text, embedding=embedding, updated_at=utcnow())
            .on_conflict(
                update={
                    AgentNote.note_text: note_text,
                    AgentNote.embedding: embedding,
                    AgentNote.updated_at: utcnow(),
                }
            )
            .execute()
        )

    def search(self, query_embedding, limit=10):
        query_vector = AgentNote.embedding.db_value(query_embedding)
        return list(
            AgentNote.select(AgentNote.note_text, AgentNote.updated_at)
            .order_by(fn.VEC_DISTANCE_COSINE(AgentNote.embedding, query_vector))
            .limit(limit)
            .dicts()
        )
