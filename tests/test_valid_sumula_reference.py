"""
Testes para o validator de súmulas citadas válidas.
"""

import sys
from pathlib import Path

# Adiciona o diretório raiz do projeto ao PYTHONPATH
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.guardrails.guards import ValidSumulaReference


def test_valid_sumulas_in_range():
    """Testa súmulas válidas dentro do range."""
    print("\n" + "=" * 60)
    print("TESTE 1: Súmulas válidas dentro do range")
    print("=" * 60)

    validator = ValidSumulaReference(min_sumula=1, max_sumula=200)

    response = """
    A Súmula 70 do TCEMG estabelece critérios para contratos.
    Conforme a Súmula nº 112, os procedimentos licitatórios
    devem seguir as normas da Súmula 85.
    """

    metadata = {
        "retrieved_sumulas": ["70", "112", "85"]
    }

    result = validator.validate(response, metadata)

    print(f"Resposta: {response[:100]}...")
    print(f"\nResultado: {result.outcome}")
    print(f"Súmulas citadas: {result.metadata.get('cited_sumulas')}")
    print(f"Súmulas inválidas: {result.metadata.get('invalid_sumulas')}")
    print(f"Fora do range: {result.metadata.get('out_of_range_sumulas')}")

    assert result.outcome == "pass", "Súmulas válidas deveriam passar"
    print("\n✅ TESTE PASSOU")


def test_sumula_out_of_range():
    """Testa súmula fora do range válido."""
    print("\n" + "=" * 60)
    print("TESTE 2: Súmula fora do range")
    print("=" * 60)

    validator = ValidSumulaReference(min_sumula=1, max_sumula=200)

    response = """
    A Súmula 70 estabelece critérios válidos.
    A Súmula 999 determina procedimentos especiais.
    """

    metadata = {
        "retrieved_sumulas": ["70", "999"]
    }

    result = validator.validate(response, metadata)

    print(f"Resposta: {response[:100]}...")
    print(f"\nResultado: {result.outcome}")
    print(f"Súmulas citadas: {result.metadata.get('cited_sumulas')}")
    print(f"Fora do range: {result.metadata.get('out_of_range_sumulas')}")
    print(f"Erro: {result.error_message if hasattr(result, 'error_message') else 'None'}")

    assert result.outcome == "fail", "Súmula 999 está fora do range"
    assert "999" in result.metadata.get('out_of_range_sumulas', [])
    print("\n✅ TESTE PASSOU - Súmula fora do range detectada")


def test_sumula_not_retrieved():
    """Testa súmula citada mas não recuperada."""
    print("\n" + "=" * 60)
    print("TESTE 3: Súmula citada mas não recuperada")
    print("=" * 60)

    validator = ValidSumulaReference(min_sumula=1, max_sumula=200)

    response = """
    A Súmula 70 estabelece critérios válidos.
    A Súmula 150 também trata do assunto.
    """

    metadata = {
        "retrieved_sumulas": ["70"]  # 150 não foi recuperada
    }

    result = validator.validate(response, metadata)

    print(f"Resposta: {response[:100]}...")
    print(f"\nResultado: {result.outcome}")
    print(f"Súmulas citadas: {result.metadata.get('cited_sumulas')}")
    print(f"Não recuperadas: {result.metadata.get('not_retrieved_sumulas')}")
    print(f"Warning: {result.metadata.get('warning', 'None')}")

    # Não é crítico, mas gera warning
    assert result.outcome == "pass", "Deveria passar mas com warning"
    assert "150" in result.metadata.get('not_retrieved_sumulas', [])
    print("\n✅ TESTE PASSOU - Warning gerado corretamente")


def test_invalid_sumula_number():
    """Testa número de súmula inválido."""
    print("\n" + "=" * 60)
    print("TESTE 4: Número de súmula inválido")
    print("=" * 60)

    validator = ValidSumulaReference(min_sumula=1, max_sumula=200)

    response = """
    A Súmula 0 não deveria existir.
    A Súmula -5 também é inválida.
    """

    metadata = {
        "retrieved_sumulas": ["0"]
    }

    result = validator.validate(response, metadata)

    print(f"Resposta: {response[:100]}...")
    print(f"\nResultado: {result.outcome}")
    print(f"Súmulas citadas: {result.metadata.get('cited_sumulas')}")
    print(f"Fora do range: {result.metadata.get('out_of_range_sumulas')}")

    assert result.outcome == "fail", "Súmula 0 é inválida"
    print("\n✅ TESTE PASSOU - Números inválidos detectados")


def test_incorrect_citation_format():
    """Testa formato de citação incorreto."""
    print("\n" + "=" * 60)
    print("TESTE 5: Formato de citação incorreto")
    print("=" * 60)

    validator = ValidSumulaReference(min_sumula=1, max_sumula=200)

    response = """
    A sumula 70 estabelece critérios (sem acento).
    A Súmula numero 85 também trata do assunto (formato incorreto).
    """

    metadata = {
        "retrieved_sumulas": ["70", "85"]
    }

    result = validator.validate(response, metadata)

    print(f"Resposta: {response[:100]}...")
    print(f"\nResultado: {result.outcome}")
    print(f"Súmulas citadas: {result.metadata.get('cited_sumulas')}")
    print(f"Issues de formato: {result.metadata.get('citation_format_issues')}")

    # Formato incorreto gera warning mas passa
    assert result.metadata.get('citation_format_issues'), "Deveria detectar formato incorreto"
    print(f"\n✅ TESTE PASSOU - {len(result.metadata.get('citation_format_issues', []))} issues de formato detectados")


def test_no_sumulas_cited():
    """Testa resposta sem súmulas citadas."""
    print("\n" + "=" * 60)
    print("TESTE 6: Resposta sem súmulas citadas")
    print("=" * 60)

    validator = ValidSumulaReference(min_sumula=1, max_sumula=200)

    response = """
    Esta resposta não menciona nenhuma súmula específica.
    Fala apenas sobre contratos e licitações em geral.
    """

    metadata = {
        "retrieved_sumulas": ["70"]
    }

    result = validator.validate(response, metadata)

    print(f"Resposta: {response[:100]}...")
    print(f"\nResultado: {result.outcome}")
    print(f"Súmulas citadas: {result.metadata.get('cited_sumulas')}")
    print(f"Validação: {result.metadata.get('validation')}")

    assert result.outcome == "pass", "Sem súmulas citadas, não há o que validar"
    assert result.metadata.get('validation') == "no_sumulas_cited"
    print("\n✅ TESTE PASSOU")


def test_with_valid_sumulas_list():
    """Testa com lista de súmulas válidas do sistema."""
    print("\n" + "=" * 60)
    print("TESTE 7: Verificação contra lista de súmulas válidas")
    print("=" * 60)

    validator = ValidSumulaReference(min_sumula=1, max_sumula=200)

    response = """
    A Súmula 70 estabelece critérios válidos.
    A Súmula 500 não existe no sistema.
    """

    metadata = {
        "retrieved_sumulas": ["70"],
        "all_valid_sumulas": ["70", "85", "100", "112"]  # Lista de súmulas que existem
    }

    result = validator.validate(response, metadata)

    print(f"Resposta: {response[:100]}...")
    print(f"\nResultado: {result.outcome}")
    print(f"Súmulas citadas: {result.metadata.get('cited_sumulas')}")
    print(f"Súmulas inválidas: {result.metadata.get('invalid_sumulas')}")
    print(f"Erro: {result.error_message if hasattr(result, 'error_message') else 'None'}")

    # 500 está fora do range E não existe na lista
    assert result.outcome == "fail"
    print("\n✅ TESTE PASSOU - Súmula inexistente detectada")


def run_all_tests():
    """Executa todos os testes."""
    print("\n" + "=" * 60)
    print("🧪 TESTES DE VALIDAÇÃO DE SÚMULAS CITADAS")
    print("=" * 60)

    try:
        test_valid_sumulas_in_range()
        test_sumula_out_of_range()
        test_sumula_not_retrieved()
        test_invalid_sumula_number()
        test_incorrect_citation_format()
        test_no_sumulas_cited()
        test_with_valid_sumulas_list()

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
