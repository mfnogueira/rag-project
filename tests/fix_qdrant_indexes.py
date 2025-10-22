"""
Script para adicionar índices de payload à coleção existente do Qdrant.
Resolve o erro: "Index required but not found for metadata.num_sumula"
"""

import sys
from pathlib import Path

# Adiciona o diretório raiz do projeto ao PYTHONPATH
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.ingest.embed_qdrant import EmbeddingSelfQuery

def add_indexes_to_existing_collection():
    """Adiciona índices necessários para self-query filtering na coleção existente."""

    embedder = EmbeddingSelfQuery()
    collection_name = "sumulas_tcemg"

    print(f"Verificando coleção '{collection_name}'...")

    if not embedder.client.collection_exists(collection_name=collection_name):
        print(f"❌ Coleção '{collection_name}' não existe!")
        return

    print(f"✅ Coleção '{collection_name}' encontrada.")
    print("\nCriando índices de payload para filtros...")

    try:
        # Índice para num_sumula (keyword)
        print("  → Criando índice para 'num_sumula' (keyword)...")
        embedder.client.create_payload_index(
            collection_name=collection_name,
            field_name="num_sumula",
            field_schema="keyword"
        )
        print("    ✅ Índice 'num_sumula' criado")

        # Índice para status_atual (keyword)
        print("  → Criando índice para 'status_atual' (keyword)...")
        embedder.client.create_payload_index(
            collection_name=collection_name,
            field_name="status_atual",
            field_schema="keyword"
        )
        print("    ✅ Índice 'status_atual' criado")

        # Índice para data_status_ano (integer)
        print("  → Criando índice para 'data_status_ano' (integer)...")
        embedder.client.create_payload_index(
            collection_name=collection_name,
            field_name="data_status_ano",
            field_schema="integer"
        )
        print("    ✅ Índice 'data_status_ano' criado")

        print("\n✅ Todos os índices foram criados com sucesso!")
        print("🎯 Self-query filtering agora funcionará corretamente.")

    except Exception as e:
        print(f"\n⚠️ Erro ao criar índices: {e}")
        print("Nota: Se o índice já existir, esse erro pode ser ignorado.")


if __name__ == "__main__":
    print("=" * 60)
    print("CORREÇÃO DE ÍNDICES DO QDRANT")
    print("=" * 60)
    add_indexes_to_existing_collection()
    print("=" * 60)
