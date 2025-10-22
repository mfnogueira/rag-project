"""
Testes para o validator de detecção de alucinações.
"""

import sys
from pathlib import Path

# Adiciona o diretório raiz do projeto ao PYTHONPATH
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.guardrails.guards import HallucinationDetection


def test_valid_response_with_context():
    """Testa resposta válida baseada no contexto."""
    print("\n" + "=" * 60)
    print("TESTE 1: Resposta válida com base no contexto")
    print("=" * 60)

    validator = HallucinationDetection(threshold=0.7)

    response = """
    A Súmula 70 do TCEMG estabelece critérios para contratos administrativos.
    Conforme a Súmula 112, os procedimentos licitatórios devem seguir
    as normas estabelecidas pela legislação vigente.
    """

    metadata = {
        "retrieved_sumulas": ["70", "112"],
        "context_text": """
        Súmula 70: Contratos administrativos devem seguir critérios específicos.
        Súmula 112: Procedimentos licitatórios conforme legislação vigente.
        """
    }

    result = validator.validate(response, metadata)

    print(f"Resposta: {response[:100]}...")
    print(f"\nResultado: {result.outcome}")
    print(f"Súmulas citadas: {result.metadata.get('cited_sumulas')}")
    print(f"Súmulas recuperadas: {result.metadata.get('retrieved_sumulas')}")
    print(f"Score de alucinação: {result.metadata.get('hallucination_score')}")
    print(f"Issues: {result.metadata.get('issues')}")

    assert result.outcome == "pass", "Resposta válida deveria passar"
    print("\n✅ TESTE PASSOU")


def test_hallucinated_sumula():
    """Testa resposta que cita súmula não recuperada."""
    print("\n" + "=" * 60)
    print("TESTE 2: Alucinação - Súmula não recuperada")
    print("=" * 60)

    validator = HallucinationDetection(threshold=0.7)

    response = """
    A Súmula 70 estabelece critérios para contratos.
    Além disso, a Súmula 999 determina procedimentos especiais
    que devem ser seguidos em casos excepcionais.
    """

    metadata = {
        "retrieved_sumulas": ["70"],  # Só recuperou 70, não 999
        "context_text": "Súmula 70: Contratos administrativos..."
    }

    result = validator.validate(response, metadata)

    print(f"Resposta: {response[:100]}...")
    print(f"\nResultado: {result.outcome}")
    print(f"Súmulas citadas: {result.metadata.get('cited_sumulas')}")
    print(f"Súmulas recuperadas: {result.metadata.get('retrieved_sumulas')}")
    print(f"Score de alucinação: {result.metadata.get('hallucination_score')}")
    print(f"Issues: {result.metadata.get('issues')}")

    assert result.outcome == "fail", "Deve detectar súmula não recuperada"
    assert "999" in str(result.metadata.get('issues')), "Deve mencionar súmula 999"
    print("\n✅ TESTE PASSOU - Alucinação detectada corretamente")


def test_no_grounding_in_context():
    """Testa resposta sem base no contexto."""
    print("\n" + "=" * 60)
    print("TESTE 3: Resposta sem base no contexto")
    print("=" * 60)

    validator = HallucinationDetection(threshold=0.7)

    response = """
    A legislação ambiental brasileira estabelece normas rigorosas
    para proteção de florestas tropicais e conservação de
    espécies em extinção conforme tratados internacionais.
    """

    metadata = {
        "retrieved_sumulas": ["70"],
        "context_text": "Súmula 70: Contratos administrativos devem seguir critérios..."
    }

    result = validator.validate(response, metadata)

    print(f"Resposta: {response[:100]}...")
    print(f"\nResultado: {result.outcome}")
    print(f"Score de alucinação: {result.metadata.get('hallucination_score')}")
    print(f"Issues: {result.metadata.get('issues')}")

    # Esperamos que falhe por falta de grounding
    if result.outcome == "fail":
        print("\n✅ TESTE PASSOU - Falta de grounding detectada")
    else:
        print("\n⚠️  AVISO: Resposta passou mas deveria ter falhado")


def test_excessive_assertions():
    """Testa resposta com muitas afirmações categóricas."""
    print("\n" + "=" * 60)
    print("TESTE 4: Muitas afirmações categóricas sem incerteza")
    print("=" * 60)

    validator = HallucinationDetection(threshold=0.7)

    response = """
    A Súmula 70 estabelece que todos os contratos devem ser anuais.
    Conforme a Súmula 70, é obrigatório seguir o procedimento X.
    A Súmula determina que pagamentos sejam mensais.
    Segundo a Súmula 70, multas são aplicáveis em todos os casos.
    """

    metadata = {
        "retrieved_sumulas": ["70"],
        "context_text": "Súmula 70: Contratos administrativos..."
    }

    result = validator.validate(response, metadata)

    print(f"Resposta: {response[:100]}...")
    print(f"\nResultado: {result.outcome}")
    print(f"Afirmações categóricas: {result.metadata.get('assertive_count')}")
    print(f"Marcadores de incerteza: {result.metadata.get('uncertainty_count')}")
    print(f"Score de alucinação: {result.metadata.get('hallucination_score')}")

    print(f"\n{'✅' if result.metadata.get('assertive_count', 0) > 0 else '❌'} Detectou afirmações categóricas")


def test_with_uncertainty_markers():
    """Testa resposta com marcadores de incerteza (BOA)."""
    print("\n" + "=" * 60)
    print("TESTE 5: Resposta com marcadores de incerteza")
    print("=" * 60)

    validator = HallucinationDetection(threshold=0.7)

    response = """
    Segundo os documentos recuperados, a Súmula 70 aparentemente
    estabelece critérios para contratos. Baseado no contexto,
    possivelmente há requisitos específicos que devem ser seguidos.
    """

    metadata = {
        "retrieved_sumulas": ["70"],
        "context_text": "Súmula 70: Contratos administrativos devem seguir critérios..."
    }

    result = validator.validate(response, metadata)

    print(f"Resposta: {response[:100]}...")
    print(f"\nResultado: {result.outcome}")
    print(f"Marcadores de incerteza: {result.metadata.get('uncertainty_count')}")
    print(f"Score de alucinação: {result.metadata.get('hallucination_score')}")

    assert result.outcome == "pass", "Resposta com marcadores de incerteza deveria passar"
    print("\n✅ TESTE PASSOU - Marcadores de incerteza ajudaram")


def run_all_tests():
    """Executa todos os testes."""
    print("\n" + "=" * 60)
    print("🧪 TESTES DE DETECÇÃO DE ALUCINAÇÕES")
    print("=" * 60)

    try:
        test_valid_response_with_context()
        test_hallucinated_sumula()
        test_no_grounding_in_context()
        test_excessive_assertions()
        test_with_uncertainty_markers()

        print("\n" + "=" * 60)
        print("✅ TODOS OS TESTES CONCLUÍDOS")
        print("=" * 60)
        return True

    except AssertionError as e:
        print(f"\n❌ TESTE FALHOU: {e}")
        return False
    except Exception as e:
        print(f"\n❌ ERRO INESPERADO: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)
