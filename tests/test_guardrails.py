"""
Script de teste para validar a implementação do Guardrails.
"""

import sys
from pathlib import Path

# Adiciona o diretório raiz do projeto ao PYTHONPATH
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.guardrails.guards import validate_input, validate_output, create_basic_guard


def test_input_validation():
    """Testa validação de inputs"""
    print("=" * 60)
    print("TESTE 1: Validação de INPUT")
    print("=" * 60)

    # Teste 1: Input normal (deve passar)
    test1 = "Qual é o conteúdo da súmula 70?"
    result1 = validate_input(test1)
    print(f"\n✓ Input limpo: '{test1}'")
    print(f"  Válido: {result1['is_valid']}")
    print(f"  Erros: {result1['errors']}")

    # Teste 2: Input com palavrão (deve falhar)
    test2 = "Me explica essa porra de súmula 70!"
    result2 = validate_input(test2)
    print(f"\n✗ Input com palavrão: '{test2}'")
    print(f"  Válido: {result2['is_valid']}")
    print(f"  Erros: {result2['errors']}")

    # Teste 3: Input com múltiplos palavrões
    test3 = "Qual é a merda da súmula 70, caralho?"
    result3 = validate_input(test3)
    print(f"\n✗ Input com múltiplos palavrões: '{test3}'")
    print(f"  Válido: {result3['is_valid']}")
    print(f"  Erros: {result3['errors']}")


def test_output_validation():
    """Testa validação de outputs"""
    print("\n" + "=" * 60)
    print("TESTE 2: Validação de OUTPUT")
    print("=" * 60)

    # Teste 1: Output normal e longo o suficiente
    test1 = "A Súmula 70 do TCEMG estabelece que... " * 10  # >100 chars
    result1 = validate_output(test1)
    print(f"\n✓ Output limpo e válido")
    print(f"  Válido: {result1['is_valid']}")
    print(f"  Tamanho: {len(test1)} chars")
    print(f"  Info: {result1['validation_info']}")

    # Teste 2: Output com linguagem tóxica
    test2 = "A súmula diz que você é um idiota se não seguir... " * 3
    result2 = validate_output(test2)
    print(f"\n✗ Output com linguagem tóxica")
    print(f"  Válido: {result2['is_valid']}")
    print(f"  Original: '{test2[:100]}...'")
    print(f"  Limpo: '{result2['cleaned_text'][:100]}...'")
    print(f"  Info: {result2['validation_info']}")

    # Teste 3: Output muito curto
    test3 = "Resposta curta"
    result3 = validate_output(test3)
    print(f"\n✗ Output muito curto")
    print(f"  Válido: {result3['is_valid']}")
    print(f"  Tamanho: {len(test3)} chars")
    print(f"  Info: {result3['validation_info']}")

    # Teste 4: Output muito longo
    test4 = "A" * 2500
    result4 = validate_output(test4)
    print(f"\n✗ Output muito longo")
    print(f"  Válido: {result4['is_valid']}")
    print(f"  Tamanho original: {len(test4)} chars")
    print(f"  Tamanho limpo: {len(result4['cleaned_text'])} chars")
    print(f"  Info: {result4['validation_info']}")


def test_guard_creation():
    """Testa criação do Guard completo"""
    print("\n" + "=" * 60)
    print("TESTE 3: Criação do Guard Completo")
    print("=" * 60)

    try:
        guard = create_basic_guard()
        print(f"\n✓ Guard criado com sucesso!")
        print(f"  Nome: {guard.name}")
        print(f"  Descrição: {guard.description}")
        print(f"  Validators: {len(guard._validators)} configurados")
    except Exception as e:
        print(f"\n✗ Erro ao criar guard: {e}")


if __name__ == "__main__":
    print("\n🛡️  TESTE DO MÓDULO GUARDRAILS")
    print("=" * 60)

    test_input_validation()
    test_output_validation()
    test_guard_creation()

    print("\n" + "=" * 60)
    print("✅ TESTES CONCLUÍDOS")
    print("=" * 60)
