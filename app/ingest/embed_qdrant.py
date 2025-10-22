from qdrant_client import QdrantClient
from app.utils.settings import settings
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_qdrant import QdrantVectorStore


class EmbeddingSelfQuery:
    def __init__(self) -> None:
        self.llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

        # Connect to Qdrant Cloud if URL is provided, otherwise use local
        if settings.QDRANT_URL and settings.QDRANT_API_KEY:
            self.client = QdrantClient(
                url=settings.QDRANT_URL,
                api_key=settings.QDRANT_API_KEY,
                timeout=120,
            )
        else:
            self.client = QdrantClient(
                host=settings.QDRANT_HOST,
                port=settings.QDRANT_PORT,
                timeout=120,
            )

        self.model = OpenAIEmbeddings(
            model="text-embedding-3-large",
        )

    def get_qdrant_vector_store(self, collection_name: str) -> QdrantVectorStore:
        return QdrantVectorStore(
            client=self.client,
            collection_name=collection_name,
            embedding=self.model,
            sparse_vector_name="text-sparse",
            vector_name="text-dense",
        )
