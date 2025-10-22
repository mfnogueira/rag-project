# 🧪 Tests & Utilities

Esta pasta contém scripts de teste e utilitários de manutenção do projeto.

## 📋 Conteúdo

### Scripts de Teste

#### `test_guardrails.py`
Testa a implementação do Guardrails AI.

**O que testa:**
- ✅ Validação de inputs (detecta palavrões e conteúdo inadequado)
- ✅ Validação de outputs (remove toxicidade, valida tamanho)
- ✅ Criação do Guard completo

**Como executar:**
```bash
uv run python tests/test_guardrails.py
```

**Saída esperada:**
```
🛡️  TESTE DO MÓDULO GUARDRAILS
============================================================
TESTE 1: Validação de INPUT
...
✅ TESTES CONCLUÍDOS
```

---

#### `test_query_complete.py`
Testa o fluxo RAG completo com uma query problemática.

**O que testa:**
- ✅ Self-Query Retriever com fallback robusto
- ✅ Guardrails de input e output
- ✅ Geração de resposta completa
- ✅ Formatação de fontes

**Como executar:**
```bash
uv run python tests/test_query_complete.py
```

**Query testada:**
```
"precedentes vigentes da sumula 70"
```

Esta query é especialmente útil porque força o LLM a gerar filtros compostos, que historicamente causavam erros de parsing.

**Saída esperada:**
```
============================================================
TESTE DE QUERY PROBLEMÁTICA
============================================================
Query: precedentes vigentes da sumula 70

⚠️ Erro no self-query filtering: ...
📝 Executando busca simples sem filtros...
🔍 Busca Semântica: precedentes vigentes da sumula 70
🛡️  Guardrails ativado - validando resposta...
✅ Resposta aprovada pelo Guardrails

[Resposta gerada...]

📚 Fontes (X documentos)
============================================================
✅ TESTE CONCLUÍDO COM SUCESSO!
```

---

### Utilitários de Manutenção

#### `fix_qdrant_indexes.py`
Script utilitário para adicionar índices de payload a uma coleção Qdrant existente.

**Quando usar:**
- ⚠️ Quando receber erro: `"Index required but not found for metadata.num_sumula"`
- 🔧 Após migrar dados de outra fonte sem índices
- 📊 Para otimizar uma coleção existente

**O que faz:**
1. Conecta no Qdrant Cloud
2. Verifica se a coleção existe
3. Cria índices para:
   - `num_sumula` (keyword) - para filtrar por número da súmula
   - `status_atual` (keyword) - para filtrar por status (VIGENTE, REVOGADA, etc.)
   - `data_status_ano` (integer) - para filtrar por ano

**Como executar:**
```bash
uv run python tests/fix_qdrant_indexes.py
```

**Saída esperada:**
```
============================================================
CORREÇÃO DE ÍNDICES DO QDRANT
============================================================
Verificando coleção 'sumulas_tcemg'...
✅ Coleção 'sumulas_tcemg' encontrada.

Criando índices de payload para filtros...
  → Criando índice para 'num_sumula' (keyword)...
    ✅ Índice 'num_sumula' criado
  → Criando índice para 'status_atual' (keyword)...
    ✅ Índice 'status_atual' criado
  → Criando índice para 'data_status_ano' (integer)...
    ✅ Índice 'data_status_ano' criado

✅ Todos os índices foram criados com sucesso!
🎯 Self-query filtering agora funcionará corretamente.
============================================================
```

**Nota:** Este script é seguro executar múltiplas vezes. Se os índices já existirem, ele apenas informará.

---

## 🚀 Executar Todos os Testes

```bash
# Teste do Guardrails
uv run python tests/test_guardrails.py

# Teste do fluxo RAG completo
uv run python tests/test_query_complete.py

# Utilitário de índices (apenas se necessário)
uv run python tests/fix_qdrant_indexes.py
```

---

## 📝 Quando Executar os Testes

### Testes Regulares (antes de deploy/commit)
- ✅ `test_guardrails.py` - Garante que validações estão funcionando
- ✅ `test_query_complete.py` - Valida fluxo RAG end-to-end

### Utilitários de Manutenção (conforme necessário)
- 🔧 `fix_qdrant_indexes.py` - Apenas quando houver erro de índice

---

## 🎯 Importância de Cada Script

| Script | Vital? | Descrição |
|--------|--------|-----------|
| `test_guardrails.py` | 📊 Teste | Valida segurança e qualidade do sistema |
| `test_query_complete.py` | 📊 Teste | Valida funcionamento end-to-end |
| `fix_qdrant_indexes.py` | 🔧 Utilitário | Correção pontual, não é parte do sistema |

**Nenhum desses scripts é vital para o funcionamento da aplicação em produção.**

Eles são ferramentas de desenvolvimento, teste e manutenção.
