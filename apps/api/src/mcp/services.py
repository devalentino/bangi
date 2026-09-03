from typing import Annotated

from peewee import fn
from wireup import Inject, injectable

from src.core.utils import log_execution_time, utcnow
from src.mcp.entities import AgentNote


@injectable(lifetime='singleton')
class EmbeddingService:
    def __init__(self, embedding_model_path: Annotated[str, Inject(config='EMBEDDING_MODEL_PATH')]):
        self.embedding_model_path = embedding_model_path

    @log_execution_time
    def compute(self, text: str) -> list[float]:
        from model2vec import StaticModel

        model = StaticModel.from_pretrained(self.embedding_model_path)
        return model.encode([text])[0].tolist()


@injectable
class AgentNoteService:
    def upsert(self, session_id, note_text, campaign_ids, embedding):
        (
            AgentNote.insert(
                session_id=session_id,
                note_text=note_text,
                campaign_ids=campaign_ids,
                embedding=embedding,
                updated_at=utcnow(),
            )
            .on_conflict(
                update={
                    AgentNote.note_text: note_text,
                    AgentNote.campaign_ids: campaign_ids,
                    AgentNote.embedding: embedding,
                    AgentNote.updated_at: utcnow(),
                }
            )
            .execute()
        )

    def search(self, query_embedding, campaign_id=None, limit=10):
        query_vector = AgentNote.embedding.db_value(query_embedding)
        query = AgentNote.select(AgentNote.note_text, AgentNote.campaign_ids, AgentNote.updated_at).order_by(
            fn.VEC_DISTANCE_COSINE(AgentNote.embedding, query_vector)
        )
        if campaign_id is not None:
            query = query.where(fn.JSON_CONTAINS(AgentNote.campaign_ids, str(campaign_id)))
        return list(query.limit(limit).dicts())
