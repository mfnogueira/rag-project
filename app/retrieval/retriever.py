from typing import List, Optional

from langchain.retrievers.self_query.base import SelfQueryRetriever
from langchain_core.documents import Document
from app.ingest.embed_qdrant import EmbeddingSelfQuery
from app.retrieval.self_query import document_content_description, metadata_field_info
from dataclasses import dataclass


@dataclass
class SelfQueryConfig:
    collection_name: str = "sumulas_tcemg"
    k: int = 10


class RobustSelfQueryRetriever(SelfQueryRetriever):
    """
    Versão robusta do SelfQueryRetriever que faz fallback quando o parsing falha.
    """

    def _get_relevant_documents(self, query: str, *, run_manager=None):
        """Override para adicionar tratamento de erros no parsing."""
        try:
            # Tenta o comportamento padrão
            return super()._get_relevant_documents(query, run_manager=run_manager)
        except Exception as e:
            # Se falhar por erro de parsing, faz busca simples
            error_msg = str(e).lower()
            if "parsing" in error_msg or "unexpected token" in error_msg:
                print(f"⚠️ Erro no self-query filtering: {e}")
                print("📝 Executando busca simples sem filtros...")
                return self.vectorstore.similarity_search(query, **self.search_kwargs)
            raise


def build_self_query_retriever(cfg: SelfQueryConfig) -> SelfQueryRetriever:
    """
    Cria o SelfQueryRetriever sobre o QdrantVectorStore com tratamento robusto de erros.
    """
    embedder = EmbeddingSelfQuery()
    vectorstore = embedder.get_qdrant_vector_store(cfg.collection_name)

    retriever = RobustSelfQueryRetriever.from_llm(
        llm=embedder.llm,
        vectorstore=vectorstore,
        document_contents=document_content_description,
        metadata_field_info=metadata_field_info,
        enable_limit=True,
        search_kwargs={"k": cfg.k},
    )

    return retriever


def search(
    query: str,
    cfg: Optional[SelfQueryConfig] = None,
) -> List[Document]:
    """
    Consulta usando self-query: o LLM infere termos SEMÂNTICOS e também FILTROS de metadado.
    """
    cfg = cfg or SelfQueryConfig()
    retriever = build_self_query_retriever(cfg)
    # .invoke() retorna List[Document]
    return retriever.invoke(query)
