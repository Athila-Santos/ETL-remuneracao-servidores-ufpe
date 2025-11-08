# Pipeline de ETL: Remuneração dos Servidores da UFPE

A transparência de dados públicos é fundamental, mas "dados abertos" raramente significam "dados fáceis". O Portal da Transparência, embora incrivelmente completo, é um verdadeiro labirinto. Uma simples pergunta como "Qual é o panorama de salários na Universidade Federal de Pernambuco?" não pode ser respondida com um único download.

Este projeto nasceu dessa curiosidade: como podemos construir um "mapa" para esse labirinto?

A resposta é este pipeline de ETL. Ele automatiza o processo de "garimpar" o portal, coletar dados de milhares de perfis de servidores e transformá-los em um **data warehouse limpo e estruturado** no Supabase (PostgreSQL). O objetivo final é ter uma fonte da verdade (single source of truth) pronta para ser consumida por qualquer ferramenta de BI (como Power BI ou Looker Studio) e responder a perguntas complexas.

## 🔭 A(s) Grande(s) Pergunta(s)

Ter os dados é bom, mas fazer as perguntas certas é o que importa. Este projeto foi construído para ser a base de um dashboard de BI que possa responder a perguntas de pesquisa interessantes sobre a estrutura da universidade:

* **Distribuição:** Qual é a real distribuição salarial? A curva é achatada? Existem "clusters" de remuneração?
* **Impacto das Funções:** Qual é o peso real de uma "função gratificada" no salário final de um servidor? É possível medir o "prêmio" por assumir uma função?
* **Carreira vs. Salário:** Existe uma correlação visível entre o tempo de casa (`data_ingresso`) e a remuneração bruta?
* **Estrutura de Vínculo:** Como a `jornada` (20h vs 40h) ou o `cargo` impactam o salário em diferentes centros ou departamentos?

## ✨ Metodologia

Este pipeline não é um único script, mas sim uma aplicação de engenharia de dados construída com foco em robustez, manutenibilidade e boas práticas.

* **Arquitetura OOP (SOLID):** O código é modularizado em classes "especialistas", cada uma com uma responsabilidade única:
    * `IdIngestor`: Cuida da ingestão da API "escondida" (Estágio 1).
    * `PortalScraper`: Especialista em raspar o HTML das páginas de perfil (Estágio 2).
    * `DataProcessor`: Limpa e formata os dados (ex: `R$ 1.234,56` -> `1234.56`).
    * `SupabaseClient`: Gerencia toda a comunicação com o banco de dados.
    * `ETLPipeline`: O "Gerente" que orquestra todos os especialistas.

* **Pipeline Robusto de 2 Estágios:**
    1.  **Estágio 1 (Ingestão):** Usa uma lógica de **"Apague e Recarregue"** (Delete/Insert). Isso garante que nossa lista mestra de servidores (`idServidores`) seja sempre um espelho 100% fiel da API, lidando automaticamente com novas contratações ou exonerações.
    2.  **Estágio 2 (Enriquecimento):** Usa uma lógica **Incremental (Delta Load)**. O pipeline é inteligente: ele compara os IDs da fonte com os que já existem no destino e raspa *apenas* o que está faltando.

* **Resiliência (Resumable):** Graças à lógica Delta + `UPSERT` um-a-um no Estágio 2, o pipeline é **"resumível"**. Se a raspagem de 6 horas for interrompida (por falha de rede ou `Ctrl+C`), você pode simplesmente rodá-la de novo. Ela "lembrará" de onde parou e continuará apenas com os IDs faltantes.

* **Testes Automatizados (CI):** Uma suíte de testes com `pytest` e `pytest-mock` garante que a lógica de parsing, formatação e a orquestração do pipeline funcionem como esperado.

* **UX de Terminal:** O loop de scraping de +7.000 itens é monitorado pelo `tqdm`, exibindo uma barra de progresso, taxa de processamento (IDs/s) e uma estimativa de tempo (ETA) clara.

## 💾 Modelo de Dados

O pipeline alimenta duas tabelas principais no Supabase, que formam a base para o modelo de dados do BI.

**Tabela 1: `idServidores`** (Alimentada pelo Estágio 1)
*Contém a lista mestra de todos os vínculos (ativos ou não) e suas funções.*

| Coluna | Tipo | Descrição |
| :--- | :--- | :--- |
| `id_portal` | `text` | O ID único do servidor (Não-único nesta tabela). |
| `situacao` | `text` | Ex: "Ativo", "Aposentado", "Pensionista". |
| `cargo` | `text` | O cargo oficial (ex: "PROFESSOR DO MAGISTERIO SUPERIOR"). |
| `funcao` | `text` | A função gratificada, se houver (ex: "FG-001"). |

**Tabela 2: `remuneracaoServidoresAtivos`** (Alimentada pelo Estágio 2)
*Contém os dados financeiros detalhados, coletados via scraping, apenas para os "Ativos".*

| Coluna | Tipo | Descrição |
| :--- | :--- | :--- |
| `id_portal` | `text` | **Chave Única (UNIQUE)**. Usada para o `UPSERT`. |
| `classe_cargo`| `text` | Nível/Classe do cargo (ex: "CLASSE C"). |
| `jornada` | `text` | Jornada de trabalho (ex: "40 HORAS SEMANAIS"). |
| `ingresso` | `date` | Data de ingresso do servidor na instituição. |
| `remuneracao_basica_bruta` | `real` | Salário bruto (numérico). |
| `remuneracao_apos_deducoes` | `real` | Salário líquido (numérico). |
| `data_coleta` | `date` | Data em que o dado foi raspado (para controle de versão). |

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
        SUPABASE_URL="httpsGas-seu-projeto-url.supabase.co"
        SUPABASE_KEY="sua-chave-anon-public-aqui"
        ```

5.  **Setup Único do Banco de Dados:**
    * Faça login no seu Supabase.
    * Vá até o **SQL Editor**.
    * Copie e rode o script SQL abaixo (que cria as tabelas `idServidores` e `remuneracaoServidoresAtivos` com a estrutura correta):
        ```sql
        -- 1. Cria a tabela principal para os IDs (Estágio 1)
        CREATE TABLE IF NOT EXISTS public."idServidores" (
            id bigserial PRIMARY KEY,
            created_at timestamp with time zone DEFAULT now() NOT NULL,
            id_portal text NOT NULL, -- Não é único
            situacao text,
            cargo text,
            funcao text
        );
        
        -- 2. Cria a tabela para os salários (Estágio 2)
        CREATE TABLE IF NOT EXISTS public."remuneracaoServidoresAtivos" (
            id bigserial PRIMARY KEY,
            created_at timestamp with time zone DEFAULT now() NOT NULL,
            id_portal text UNIQUE NOT NULL, -- Único para o UPSERT
            classe_cargo text,
            jornada text,
            ingresso date,
            remuneracao_basica_bruta real,
            remuneracao_apos_deducoes real,
            data_coleta date
        );
        ```

### 3. Como Rodar o Pipeline
Com seu `venv` ativo e o `.env` configurado, basta rodar:
```bash
python main.py
```

O pipeline iniciará. Na primeira vez, ele rodará o Estágio 1 (populando idServidores, ~1 min) e depois começará o Estágio 2 (raspando os ~7.000 IDs, ~6-7 horas). Se você parar e rodar de novo, ele pulará os IDs já processados.