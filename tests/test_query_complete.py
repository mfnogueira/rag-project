"""
Teste completo do fluxo RAG com query problemática.
"""

import sys
from pathlib import Path

# Adiciona o diretório raiz do projeto ao PYTHONPATH
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.graph.rag_graph import run_streaming_rag

def test_problematic_query():
    """Testa query que causava erro de parsing antes."""

    print("=" * 60)
    print("TESTE DE QUERY PROBLEMÁTICA")
    print("=" * 60)

    query = "precedentes vigentes da sumula 70"
    print(f"\nQuery: {query}\n")

    try:
        for event in run_streaming_rag(query):
            event_type = event.get("type")

            if event_type == "details":
                data = event.get("data", {})
                print(f"🔍 Busca Semântica: {data.get('query')}")
                print(f"🔧 Filtros: {data.get('filter')}\n")

            elif event_type == "token":
                # Imprime tokens da resposta
                print(event.get("data"), end="", flush=True)

            elif event_type == "sources":
                sources = event.get("data", [])
                print(f"\n\n📚 Fontes ({len(sources)} documentos):")
                for i, src in enumerate(sources[:3], 1):
                    print(f"  {i}. Súmula {src.get('num_sumula')} - {src.get('status_atual')}")

            elif event_type == "error":
                print(f"\n❌ Erro: {event.get('data')}")
                return False

        print("\n\n" + "=" * 60)
        print("✅ TESTE CONCLUÍDO COM SUCESSO!")
        print("=" * 60)
        return True

    except Exception as e:
        print(f"\n❌ Erro inesperado: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_problematic_query()
    exit(0 if success else 1)
