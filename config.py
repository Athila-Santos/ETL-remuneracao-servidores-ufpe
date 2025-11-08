import os
from dotenv import load_dotenv

# --- 1. Carregar Variáveis de Ambiente ---
load_dotenv()

# --- 2. Credenciais e Configurações do Supabase ---
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

TABELA_IDS = "idServidores"
TABELA_REMUNERACAO = "remuneracaoServidoresAtivos"

# --- 3. Configurações do Scraper ---
# URL base para a consulta de servidores
BASE_URL_SERVIDORES = "https://portaldatransparencia.gov.br/servidores"

XPATH_CLASSE_CARGO = '//*[@id="collapse-1"]/div/div[1]/div[2]/span'
XPATH_JORNADA = '//*[@id="collapse-1"]/div/div[4]/div[1]/span'
XPATH_INGRESSO = '//*[@id="collapse-1"]/div/div[6]/div[1]/span'
XPATH_REMUNERACAO_BASICA = '//*[@id="tab-remuneracoesServidor-2-servidor-civil"]/div/div[2]/div[2]/span'
XPATH_REMUNERACAO_LIQUIDA = '//*[@id="tab-remuneracoesServidor-2-servidor-civil"]/div/div[4]/div[2]/strong'

# --- 4. Configurações do Ingestor ---

API_URL_INGESTAO = 'https://portaldatransparencia.gov.br/servidores/consulta/resultado?paginacaoSimples=true&tamanhoPagina=80000&offset=0&direcaoOrdenacao=asc&colunaOrdenacao=nome&orgaosServidorLotacao=OR26242&colunasSelecionadas=detalhar%2Ctipo%2Ccpf%2Cnome%2CorgaoServidorLotacao%2Cmatricula%2Csituacao%2Cfuncao%2Ccargo%2Cquantidade&t=1AEX07LmbjkXuFbhignd&_=1719571776208'

API_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.93 Safari/537.36'
}