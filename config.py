import os
from dotenv import load_dotenv

# --- 1. Carregar Variáveis de Ambiente ---
load_dotenv()

# --- 2. Credenciais e Configurações do Supabase ---
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

TABELA_IDS = "idServidores" 
TABELA_REMUNERACAO = "remuneracaoServidoresAtivos" 

# --- 3. Configurações do Ingestor (Estágio 1) ---
API_URL_INGESTAO = 'https://portaldatransparencia.gov.br/servidores/consulta/resultado?paginacaoSimples=true&tamanhoPagina=80000&offset=0&direcaoOrdenacao=asc&colunaOrdenacao=nome&orgaosServidorLotacao=OR26242&colunasSelecionadas=detalhar%2Ctipo%2Ccpf%2Cnome%2CorgaoServidorLotacao%2Cmatricula%2Csituacao%2Cfuncao%2Ccargo%2Cquantidade&t=1AEX07LmbjkXuFbhignd&_=1719571776208'
API_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.93 Safari/537.36'
}

# --- 4. Configurações do Scraper (Estágio 2) ---
BASE_URL_SERVIDORES = "https://portaldatransparencia.gov.br/servidores"

# --- 5. Mapeamento de XPaths (v3 - Corrigido para <strong>) ---
# Lógica: Encontre a tag <strong> que contém o rótulo e pegue o <span> irmão.

# -- Seção "Vínculo" (section[2] / id="collapse-1") --
XPATH_CARGO_EMPREGO = "//strong[contains(text(), 'Cargo/Emprego:')]/following-sibling::span"
XPATH_CLASSE_CARGO = "//strong[contains(text(), 'Classe do Cargo:')]/following-sibling::span"
XPATH_REGIME_JURIDICO = "//strong[contains(text(), 'Regime Jurídico:')]/following-sibling::span"
XPATH_JORNADA = "//strong[contains(text(), 'Jornada de Trabalho:')]/following-sibling::span"
XPATH_INGRESSO_ORGAO = "//strong[contains(text(), 'ingresso no Órgão de lotação:')]/following-sibling::span"
XPATH_INGRESSO_SERVICO_PUBLICO = "//strong[contains(text(), 'ingresso no serviço público:')]/following-sibling::span"
XPATH_FORMA_INGRESSO = "//strong[contains(text(), 'Forma de ingresso no serviço público:')]/following-sibling::span"
XPATH_AFASTAMENTO = "//strong[contains(text(), 'Afastamento:')]/following-sibling::span"
XPATH_UORG = "//strong[contains(text(), 'UORG:')]/following-sibling::span"

# -- Seção "Remuneração" (section[3]) --
# (Aba de data ativa)
XPATH_DATA_REMUNERACAO = "//section[3]//nav/ul/li[contains(@class, 'active')]/button"

# (Valores de salário) - Esta lógica é diferente, busca o rótulo e sobe para o pai.
XPATH_REMUNERACAO_BASICA = "//span[contains(text(), 'Remuneração básica bruta:')]/ancestor::div[1]/following-sibling::div[1]/span"
XPATH_REMUNERACAO_LIQUIDA = "//strong[contains(text(), 'Total da Remuneração Após Deduções:')]/ancestor::div[1]/following-sibling::div[1]/strong"