# 🏛️ Assistente de Súmulas TCEMG

Sistema de RAG (Retrieval-Augmented Generation) para consulta inteligente de súmulas do Tribunal de Contas do Estado de Minas Gerais.

## 📋 Visão Geral

Este projeto implementa um assistente conversacional baseado em IA que permite realizar consultas em linguagem natural sobre súmulas do TCEMG. O sistema utiliza técnicas avançadas de RAG com Self-Query para inferir automaticamente filtros de metadados e realizar buscas semânticas precisas.

### ✨ Funcionalidades

- 🔍 **Busca Semântica Híbrida**: Vetores densos e esparsos para máxima precisão
- 🤖 **Self-Query Retriever**: Extração automática de filtros a partir da pergunta
- 💬 **Interface Conversacional**: Chat interativo via Streamlit
- 📊 **Observabilidade Completa**: Rastreamento detalhado com Langfuse
- ☁️ **Cloud-Ready**: Suporte a Qdrant Cloud e local
- 📚 **Processamento Automático**: Extração de metadados e chunks dos PDFs

### 🛠️ Stack Tecnológica

| Componente | Tecnologia | Propósito |
|------------|-----------|-----------|
| **LLM** | OpenAI GPT-4o-mini | Geração de respostas e análise de documentos |
| **Embeddings** | text-embedding-3-large | Vetorização semântica (3072 dimensões) |
| **Vector Store** | Qdrant Cloud | Armazenamento e busca vetorial |
| **Orquestração** | LangGraph | Controle de fluxo e estado |
| **Framework** | LangChain | Integração LLM + Vector Store |
| **Observabilidade** | Langfuse | Monitoramento e traces |
| **Interface** | Streamlit | Frontend interativo |
| **Extração PDF** | MarkItDown | Processamento de documentos |
| **Gerenciador** | uv | Gestão de dependências Python |

---

## 🏗️ Arquitetura

```
┌─────────────┐
│   Usuário   │
└──────┬──────┘
       │ Pergunta
       ▼
┌─────────────────────────────────────┐
│        Streamlit Interface          │
└──────────────┬──────────────────────┘
               │
               ▼
┌──────────────────────────────────────┐
│         LangGraph Workflow           │
│  ┌────────────┐    ┌──────────────┐ │
│  │  Retrieve  │───▶│   Generate   │ │
│  └────────────┘    └──────────────┘ │
└──────────────┬───────────────────────┘
               │
      ┌────────┴────────┐
      ▼                 ▼
┌─────────────┐   ┌──────────┐
│   Qdrant    │   │  OpenAI  │
│   Cloud     │   │   API    │
└─────────────┘   └──────────┘
      │
      ▼
┌─────────────┐
│  Langfuse   │
│ Monitoring  │
└─────────────┘
```

### Fluxo de Dados

1. **Input**: Usuário faz pergunta em linguagem natural
2. **Self-Query**: LLM analisa a pergunta e extrai:
   - Termos semânticos para busca
   - Filtros de metadados (status, ano, número da súmula)
3. **Retrieval**: Busca híbrida no Qdrant retorna chunks relevantes
4. **Generation**: GPT-4o-mini gera resposta contextualizada
5. **Output**: Resposta + fontes são exibidas no chat

---

## 📁 Estrutura do Projeto

```
rag-project/
├── app/
│   ├── graph/
│   │   ├── rag_graph.py          # Orquestração LangGraph
│   │   └── prompt.py             # Templates de prompts
│   ├── ingest/
│   │   ├── embed_qdrant.py       # Cliente Qdrant + Embeddings
│   │   └── extract_text.py       # Pipeline de ingestão
│   ├── retrieval/
│   │   ├── retriever.py          # Self-Query Retriever
│   │   └── self_query.py         # Definição de metadados
│   └── utils/
│       └── settings.py           # Configurações
├── sumulas/                      # PDFs das súmulas (125 arquivos)
├── app.py                        # Interface Streamlit
├── pyproject.toml                # Dependências (uv)
├── .env                          # Variáveis de ambiente
└── README.md
```

---

## 🚀 Início Rápido

### Pré-requisitos

- **Python 3.12+**
- **uv** (gerenciador de pacotes Python)
- Contas nas plataformas:
  - [OpenAI](https://platform.openai.com/) (API key)
  - [Qdrant Cloud](https://cloud.qdrant.io/) (cluster + API key)
  - [Langfuse](https://cloud.langfuse.com/) (opcional, para observabilidade)

### 1️⃣ Instalação do uv

**Linux/macOS/WSL:**
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
export PATH="$HOME/.local/bin:$PATH"
```

**Windows (PowerShell):**
```powershell
irm https://astral.sh/uv/install.ps1 | iex
```

### 2️⃣ Clone e Configure

```bash
git clone https://github.com/mfnogueira/rag-project.git
cd rag-project
```

### 3️⃣ Configurar Variáveis de Ambiente

Crie um arquivo `.env` na raiz do projeto:

```env
# OpenAI
OPENAI_API_KEY=sk-proj-xxxxxxxxxxxxxxxxxx

# Qdrant Cloud
QDRANT_URL=https://seu-cluster.cloud.qdrant.io:6333
QDRANT_API_KEY=sua-api-key-aqui

# Langfuse (opcional)
LANGFUSE_PUBLIC_KEY=pk-lf-xxxxxxxxxx
LANGFUSE_SECRET_KEY=sk-lf-xxxxxxxxxx
LANGFUSE_HOST=https://us.cloud.langfuse.com
```

> **💡 Dica**: Para obter as credenciais do Qdrant Cloud, acesse o [painel](https://cloud.qdrant.io/), crie um cluster gratuito e copie a URL e API Key.

### 4️⃣ Instalar Dependências

**Linux/macOS/WSL:**
```bash
uv sync
```

**Windows (se houver erro de permissão):**
```bash
export UV_LINK_MODE=copy
uv sync
```

### 5️⃣ Adicionar Documentos

Coloque os PDFs das súmulas na pasta `sumulas/`.

> 📄 Os PDFs oficiais estão disponíveis em: [TCE-MG Súmulas](https://www.tce.mg.gov.br/Noticia/Detalhe/67)

### 6️⃣ Ingestão dos Documentos

Execute o pipeline de ingestão para processar os PDFs e criar a coleção no Qdrant:

```bash
uv run python -m app.ingest.extract_text
```

**O que acontece durante a ingestão:**
- ✅ Extração de texto dos PDFs (125 documentos)
- ✅ Análise com GPT-4o-mini para extrair metadados
- ✅ Divisão em chunks (conteúdo, referências, precedentes)
- ✅ Geração de embeddings (text-embedding-3-large)
- ✅ Inserção no Qdrant Cloud (~359 chunks)

⏱️ **Tempo estimado**: 10-20 minutos (depende da API da OpenAI)

### 7️⃣ Executar a Aplicação

```bash
uv run streamlit run app.py
```

Acesse: **http://localhost:8501**

---

## 💬 Exemplos de Uso

### Consultas Básicas

```
"O que diz a súmula 70?"
"Quais súmulas falam sobre licitação?"
"Me explique a súmula 100"
```

### Consultas com Filtros Automáticos

```
"Súmulas vigentes sobre contratos administrativos"
→ Filtro automático: status_atual = "VIGENTE"

"Quais súmulas foram alteradas em 2014?"
→ Filtro automático: data_status_ano = 2014

"Precedentes da súmula 70 vigente"
→ Filtros: num_sumula = "70" E status_atual = "VIGENTE"
```

### Consultas Complexas

```
"Compare as súmulas 50 e 60 sobre prestação de contas"
"Quais súmulas revogadas tratavam de servidores públicos?"
"Me mostre todas as referências normativas da súmula 85"
```

---

## 🔧 Configurações Avançadas

### Ajustar Número de Documentos Recuperados

Edite `app/retrieval/retriever.py`:

```python
@dataclass
class SelfQueryConfig:
    collection_name: str = "sumulas_tcemg"
    k: int = 10  # ← Altere aqui (padrão: 10)
```

### Usar Qdrant Local (Docker)

Se preferir rodar o Qdrant localmente ao invés do Cloud:

```bash
docker run -d --name qdrant -p 6333:6333 qdrant/qdrant
```

No `.env`, troque para:
```env
QDRANT_URL=http://localhost:6333
QDRANT_API_KEY=  # Deixe vazio para local
```

### Alterar Modelo LLM

Edite `app/ingest/embed_qdrant.py`:

```python
self.llm = ChatOpenAI(
    model="gpt-4o-mini",  # Ou: "gpt-4o", "gpt-4-turbo"
    temperature=0
)
```

---

## 📊 Observabilidade

### Langfuse Dashboard

Acesse [https://cloud.langfuse.com](https://cloud.langfuse.com) para visualizar:

- 📈 **Métricas**: Tokens, latência, custos
- 🔍 **Traces**: Fluxo completo de cada consulta
- 💬 **Prompts**: Templates usados
- 🐛 **Debug**: Erros e exceptions

### Metadados Rastreados

Cada execução registra:
- `collection`: Nome da coleção Qdrant
- `k`: Número de documentos recuperados
- `tags`: `["rag-tcemg", "sumulas"]`

---

## 🧮 Detalhes Técnicos

### Metadados Estruturados

Cada chunk possui os seguintes metadados:

| Campo | Tipo | Exemplo | Descrição |
|-------|------|---------|-----------|
| `num_sumula` | string | "70" | Número da súmula |
| `status_atual` | string | "VIGENTE" | Status atual |
| `data_status` | string | "07/04/14" | Data formatada |
| `data_status_ano` | integer | 2014 | Ano (para filtros numéricos) |
| `pdf_name` | string | "Súmula 070-89.pdf" | Nome do arquivo |
| `chunk_type` | string | "conteudo_principal" | Tipo do chunk |
| `chunk_index` | integer | 0 | Índice do chunk |

### Por Que Armazenar Ano como Inteiro?

O Qdrant só suporta comparações (`<`, `>`, `>=`, `<=`) em campos numéricos. Como as datas originais vêm no formato `DD/MM/AA`, não é possível fazer:

```python
# ❌ Não funciona (comparação lexicográfica)
"01/01/10" > "31/12/09"  # Retorna False (incorreto!)

# ✅ Funciona (comparação numérica)
2010 > 2009  # Retorna True
```

Por isso, durante a ingestão, extraímos apenas o ano como inteiro no campo `data_status_ano`.

### Tipos de Chunks

Cada súmula é dividida em até 3 chunks:

1. **conteudo_principal**: Texto vigente da súmula
2. **referencias_normativas**: Legislação relacionada
3. **precedentes**: Jurisprudência e casos anteriores

---

## 📚 Referências

### Documentação Oficial

- [LangChain](https://python.langchain.com/docs/introduction/)
- [LangGraph](https://langchain-ai.github.io/langgraph/)
- [Qdrant](https://qdrant.tech/documentation/)
- [Langfuse](https://langfuse.com/docs)
- [Streamlit](https://docs.streamlit.io/)
- [MarkItDown](https://github.com/microsoft/markitdown)

### APIs Utilizadas

- [OpenAI API](https://platform.openai.com/docs/api-reference)
- [Qdrant REST API](https://qdrant.tech/documentation/interfaces/)

### Artigos e Papers

- [RAG: Retrieval-Augmented Generation](https://arxiv.org/abs/2005.11401)
- [Self-Query Retrieval](https://blog.langchain.dev/query-construction/)

---

## 🤝 Contribuindo

Contribuições são bem-vindas! Para contribuir:

1. Fork o projeto
2. Crie uma branch para sua feature (`git checkout -b feature/MinhaFeature`)
3. Commit suas mudanças (`git commit -m 'Adiciona MinhaFeature'`)
4. Push para a branch (`git push origin feature/MinhaFeature`)
5. Abra um Pull Request

---

## 📄 Licença

Este projeto está sob a licença MIT. Veja o arquivo [LICENSE](LICENSE) para mais detalhes.

---

⭐ **Se este projeto foi útil para você, considere dar uma estrela no [GitHub](https://github.com/mfnogueira/rag-project)!**
