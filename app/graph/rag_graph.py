from typing import Annotated, List, Dict, Any, Generator, TypedDict
import re

from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langchain_core.structured_query import StructuredQuery
from langfuse.langchain import CallbackHandler
from langchain_core.runnables import RunnableConfig

from app.ingest.embed_qdrant import EmbeddingSelfQuery
from app.retrieval.retriever import build_self_query_retriever, SelfQueryConfig
from app.graph.prompt import SYSTEM_PROMPT_JURIDICO

langfuse_handler = CallbackHandler()


# Definição do Estado do Grafo
class RAGState(TypedDict):
    question: str
    docs: List[Document]
    answer: Generator[str, None, None]
    generated_query: str
    generated_filter: str
    messages: Annotated[list, add_messages]


# --- Funções Auxiliares ---
def _format_filter_for_display(filter_obj: Any) -> str:
    """Formata o filtro do LangChain para uma exibição mais amigável."""
    if not filter_obj:
        return "Nenhum filtro aplicado."
    raw_str = str(filter_obj)
    raw_str = re.sub(r"Operation\(operator=<Operator\..*?>,\s*arguments=", "", raw_str)
    raw_str = re.sub(
        r"Comparator\(attribute='(.*?)',\s*operator=<Comparator\..*?>,\s*value='(.*?)'\)",
        r"\1 = '\2'",
        raw_str,
    )
    raw_str = raw_str.replace("[", "").replace("]", "").replace("),", " E ")
    raw_str = raw_str.strip("()")
    return raw_str if raw_str else "Nenhum filtro aplicado."


def _format_docs(docs: List[Document]) -> str:
    parts = []
    for d in docs:
        md = d.metadata or {}
        head = (
            f"[{md.get('pdf_name', '?')} | Súmula {md.get('num_sumula', '?')} | {md.get('chunk_type', 'chunk')}]"
            f"\nstatus_atual: {md.get('status_atual', 'não informado')}"
            f"\ndata_status: {md.get('data_status', 'não informado')}"
        )
        parts.append(f"{head}\n\n{d.page_content}")
    return "\n\n---\n\n".join(parts)


# --- Nós do Grafo ---
def retrieve(
    state: RAGState,
    config: RunnableConfig,
    collection_name: str = "sumulas_tcemg",
    k: int = 5,
) -> Dict[str, Any]:
    """Nó que executa o SelfQueryRetriever e extrai os detalhes da consulta gerada."""
    print("Executando o nó de recuperação...")
    cfg = SelfQueryConfig(collection_name=collection_name, k=k)
    retriever = build_self_query_retriever(cfg)

    try:
        structured_query: StructuredQuery = retriever.query_constructor.invoke(
            {"query": state["question"]}, config=config
        )
        docs = retriever.invoke(state["question"], config=config)
    except Exception as e:
        # Se falhar, tenta busca simples sem filtros
        print(f"⚠️ Erro no self-query: {e}")
        print("Executando busca simples sem filtros...")
        embedder = EmbeddingSelfQuery()
        vectorstore = embedder.get_qdrant_vector_store(collection_name)
        docs = vectorstore.similarity_search(state["question"], k=k)
        structured_query = StructuredQuery(query=state["question"], filter=None)

    print(f"Busca finalizada. Encontrados {len(docs)} documentos.")
    return {
        "docs": docs,
        "generated_query": structured_query.query,
        "generated_filter": _format_filter_for_display(structured_query.filter),
    }


def generate_stream(state: RAGState, config: RunnableConfig) -> Dict[str, Any]:
    """Nó que gera a resposta final em formato de stream com validação Guardrails."""
    print("Executando o nó de geração...")
    from app.guardrails.guards import validate_output

    QA_PROMPT = ChatPromptTemplate.from_messages(
        [
            ("system", SYSTEM_PROMPT_JURIDICO),
            (
                "human",
                "Pergunta: {question}\n\nContexto (trechos):\n{context}\n\nResponda de forma direta. Ao final, liste fontes no formato: (Status da Súmula: metadata.status_atual, Número da Súmula: metadata.num_sumula, Data da Publicação:  metadata.data_status).",
            ),
        ]
    )

    embedder = EmbeddingSelfQuery()
    llm = embedder.llm
    context = _format_docs(state.get("docs", []))
    chain = QA_PROMPT | llm | StrOutputParser()

    # Acumular resposta completa para validação
    print("🛡️  Guardrails ativado - validando resposta...")
    full_answer = ""
    for chunk in chain.stream(
        {"question": state["question"], "context": context},
        config=config,
    ):
        full_answer += chunk

    # Validar resposta completa com detecção de alucinações
    docs = state.get("docs", [])
    validation_result = validate_output(
        full_answer,
        context_docs=docs,
        enable_hallucination_detection=True
    )
    validated_answer = validation_result["cleaned_text"]

    if not validation_result["is_valid"]:
        print(f"⚠️  Resposta ajustada pelo Guardrails: {validation_result['validation_info']}")
    else:
        print("✅ Resposta aprovada pelo Guardrails")

    # Retornar como generator para manter compatibilidade
    def answer_generator():
        for char in validated_answer:
            yield char

    return {"answer": answer_generator()}


# --- Construção do Grafo ---
def build_streaming_graph(collection_name: str = "sumulas_tcemg", k: int = 5):
    """Compila o grafo LangGraph com os nós para streaming."""
    graph = StateGraph(RAGState)
    graph.add_node(
        "retrieve",
        lambda s, config: retrieve(
            s, config=config, collection_name=collection_name, k=k
        ),
    )
    graph.add_node("generate", generate_stream)
    graph.set_entry_point("retrieve")
    graph.add_edge("retrieve", "generate")
    graph.add_edge("generate", END)
    return graph.compile()


# Instância única do grafo compilado para ser reutilizada
COMPILED_GRAPH = build_streaming_graph()


# --- Função Principal (Ponto de Entrada para o Frontend) ---
def run_streaming_rag(question: str) -> Generator[Dict[str, Any], None, None]:
    """
    Função de alto nível que executa o fluxo RAG com validação Guardrails.
    """
    from app.guardrails.guards import validate_input

    # Validar input do usuário
    input_validation = validate_input(question)

    if not input_validation["is_valid"]:
        # Retorna erro se input contém conteúdo inadequado
        yield {
            "type": "error",
            "data": {
                "message": "Pergunta contém conteúdo inadequado",
                "errors": input_validation["errors"]
            }
        }
        return

    # run_config = {"callbacks": [langfuse_handler], "run_name": "Chat"}
    run_config = RunnableConfig(
        callbacks=[langfuse_handler],
        run_name="Chat",
        tags=["rag-tcemg", "sumulas"],
        metadata={"collection": "sumulas_tcemg", "k": 5},
    )

    initial_state: RAGState = {"question": question, "messages": []}
    final_state = {}

    # Executa o grafo em modo streaming
    for event in COMPILED_GRAPH.stream(initial_state, config=run_config):
        if "retrieve" in event:
            output = event["retrieve"]
            yield {
                "type": "details",
                "data": {
                    "query": output["generated_query"],
                    "filter": output["generated_filter"],
                },
            }

        if "generate" in event:
            answer_stream = event["generate"]["answer"]
            # Itera sobre o gerador de tokens da resposta
            for token in answer_stream:
                yield {"type": "token", "data": token}

        if END in event:
            final_state = event[END]

    # Formata e retorna as fontes no final do fluxo
    docs = final_state.get("docs", [])
    sources = [
        {
            "pdf_name": d.metadata.get("pdf_name"),
            "data_status": d.metadata.get("data_status"),
            "data_status_ano": d.metadata.get("data_status_ano"),
            "status_atual": d.metadata.get("status_atual"),
            "num_sumula": d.metadata.get("num_sumula"),
            "chunk_type": d.metadata.get("chunk_type"),
        }
        for d in docs
    ]
    yield {"type": "sources", "data": sources}
