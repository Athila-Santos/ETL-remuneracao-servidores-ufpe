# Pipeline de dados: Remuneração dos Servidores da UFPE

![Python](https://img.shields.io/badge/Python-3.13-blue?logo=python&style=for-the-badge)
![Pytest](https://img.shields.io/badge/Testes-Pytest-green?logo=pytest&style=for-the-badge)
![CI/CD](https://img.shields.io/badge/CI/CD-GitHub_Actions-blueviolet?logo=githubactions&style=for-the-badge)
![Database](https://img.shields.io/badge/Database-Supabase-darkgreen?logo=supabase&style=for-the-badge)
![BI](https://img.shields.io/badge/BI-Power_BI-yellow?logo=powerbi&style=for-the-badge)

> ## [📍 Ver o Dashboard Interativo (Power BI)](https://app.powerbi.com/view?r=eyJrIjoiNTMzODkwOTMtZGZlZS00MzY3LWJkODktOWUzNTNjZGExZTQ5IiwidCI6ImUyZjc3ZDAwLTAxNjMtNGNmNi05MmIwLTQ4NGJhZmY5ZGY3ZCJ9)

![Print do Dashboard](/docs/dashboard.png)

Este projeto é um pipeline de dados de ponta-a-ponta que extrai, transforma e carrega dados de remuneração de servidores do Portal da Transparência em um data warehouse no Supabase (PostgreSQL). O pipeline é 100% automatizado via GitHub Actions e os dados são consumidos em um dashboard interativo no Power BI.

---

## 🚀 Status do Pipeline (CI/CD)

O pipeline é orquestrado via GitHub Actions e está configurado para rodar em agendamento (cron) ou manualmente (`workflow_dispatch`). O status do último *run* na branch `main` é:

![Status do Pipeline ETL](/docs/actions.png)

## ✨ Destaques da Arquitetura

O projeto foi desenhado com foco em robustez, escalabilidade e boas práticas de engenharia de dados:

* **Arquitetura OOP (SOLID):** O código é modularizado em classes "especialistas" com responsabilidade única (`IdIngestor`, `PortalScraper`, `DataProcessor`, `SupabaseClient`, `ETLPipeline`).
* **Pipeline Robusto de 2 Estágios:**
    1.  **Estágio 1 (Ingestão):** Usa "Apague e Recarregue" (Delete/Insert) da API "escondida" do portal. Inclui uma lógica de **pré-agregação** para fundir registros duplicados (ex: Cargo + Função) antes de carregar na tabela mestra.
    2.  **Estágio 2 (Enriquecimento):** Usa **Delta Load (Incremental)**. O pipeline compara a fonte e o destino (`set_fonte - set_destino`) e raspa *apenas* os IDs faltantes.
* **Resiliência (Resumable):** Graças à lógica Delta + `UPSERT` um-a-um, o pipeline é "resumível". Se a raspagem de +6 horas for interrompida (por `Ctrl+C` ou pelo *timeout* de 6h do Actions), ele continua de onde parou na próxima execução.
* **Testes Automatizados (CI):** Suíte de testes com `pytest` e `pytest-mock` garante a lógica de parsing, formatação e orquestração.
* **Robustez de Scrape:**
    * **XPaths Relativos:** Usa XPaths robustos baseados em `contains(text(), '...')` (ex: `//strong[...]`) em vez de caminhos absolutos frágeis.
    * **Controle de Firewall:** Inclui `time.sleep(1)` no loop de scrape para evitar `ConnectionResetError` (10054) do host.
* **UX de Terminal:** O loop de scraping é monitorado pelo `tqdm`, exibindo uma barra de progresso clara, taxa de processamento (IDs/s) e um ETA.

---

## 🛠️ Como Instalar e Rodar

### 1. Pré-requisitos
* Python 3.10+
* Uma conta gratuita no [Supabase](https://supabase.com/)

### 2. Instalação Local
1.  **Clone o repositório:**
    ```bash
    git clone https://github.com/Athila-Santos/ETL-salarios-servidores-ufpe
    cd ETL-salarios-servidores-ufpe
    ```
2.  **Crie e ative um ambiente virtual:**
    ```bash
    python -m venv venv
    source venv/bin/activate  # (Linux/Mac)
    .\venv\Scripts\activate   # (Windows)
    ```
3.  **Instale as dependências:**
    ```bash
    pip install -r requirements.txt
    ```
4.  **Configure suas credenciais:**
    * Crie um arquivo chamado `.env` na raiz do projeto.
    * Adicione suas chaves do Supabase (encontradas em *Project Settings* > *API*):
        ```ini
        # .env
        SUPABASE_URL=https://seu-projeto-url.supabase.co
        SUPABASE_KEY=sua-chave-anon-public-aqui
        ```
5.  **Setup Único do Banco de Dados:**
    * Faça login no seu Supabase e vá até o **SQL Editor**.
    * Copie e cole o código abaixo para criar as tabelas `idServidores` e `remuneracaoServidoresAtivos`.
        ```sql
        CREATE TABLE IF NOT EXISTS public."idServidores" 
        (id bigserial PRIMARY KEY,
        created_at timestamp with time zone DEFAULT now() NOT NULL,
        id_portal text NOT NULL, -- Coluna de conflito
        situacao text,
        cargo text,
        funcao text);
        
        CREATE TABLE IF NOT EXISTS public."remuneracaoServidoresAtivos" 
        (id bigserial PRIMARY KEY,
        created_at timestamp with time zone DEFAULT now() NOT NULL,
        -- Chave principal para o UPSERT
        id_portal text UNIQUE NOT NULL, 
        
        -- Dados de Vínculo (Raspados)
        cargo_emprego text,
        classe_cargo text,
        regime_juridico text,
        jornada text,
        afastamento text,
        
        -- Dados de Lotação (Raspados)
        uorg_lotacao text,
        
        -- Dados de Ingresso (Raspados)
        ingresso_orgao date,
        ingresso_servico_publico date,
        forma_ingresso text,
        
        -- Dados Financeiros (Raspados)
        remuneracao_basica_bruta real,
        remuneracao_apos_deducoes real,
        
        -- Metadados de Data (Essenciais para o BI)
        data_remuneracao text, -- O mês/ano da folha de pagamento (ex: 2025-10-01)
        data_coleta date      -- O dia em que o scrape foi executado (ex: 2025-11-07));
        ```

### 3. Como Rodar o Pipeline
Com seu `venv` ativo e o `.env` configurado, basta rodar:
```bash
python main.py
````

O pipeline iniciará, calculará o "delta" (na primeira vez, todos os \~7.000 IDs) e começará o scraping.

### 4\. Como Rodar os Testes

```bash
pytest
```

-----

## 💾 Modelo de Dados

O pipeline alimenta duas tabelas principais no Supabase:

**Tabela 1: `idServidores`** (Alimentada pelo Estágio 1)
| Coluna | Tipo | Descrição |
| :--- | :--- | :--- |
| `id_portal` | `text` | ID do servidor (Não-único, agregado). |
| `situacao` | `text` | Ex: "Ativo", "Aposentado". |
| `cargo` | `text` | O cargo principal. |
| `funcao` | `text` | A função gratificada (agregada). |

**Tabela 2: `remuneracaoServidoresAtivos`** (Alimentada pelo Estágio 2)
| Coluna | Tipo | Descrição |
| :--- | :--- | :--- |
| `id_portal` | `text` | **Chave Única (UNIQUE)**. Usada para o `UPSERT`. |
| `cargo_emprego`| `text` | Cargo detalhado (do scrape). |
| `uorg_lotacao`| `text` | Lotação do servidor (ex: "HC - ..."). |
| `jornada` | `text` | Ex: "40 HORAS SEMANAIS". |
| `ingresso_servico_publico` | `date` | Data de ingresso. |
| ... | ... | ... |
| `data_remuneracao` | `text` | Mês/Ano do salário (ex: "Setembro 2025"). |
| `data_coleta` | `date` | Data em que o dado foi raspado. |

## 🔭 Contexto e Perguntas de Pesquisa

Este projeto nasceu da curiosidade em responder perguntas que um simples "dado aberto" não responde:

  * **Distribuição:** Qual é distribuição salarial dos servidores ativos da UFPE?
  * **Impacto das Funções:** Qual é a relevância e presença das funções gratificadas?
  * **Carreira vs. Salário:** Existe relação entre o tempo de serviço e o salário bruto?
