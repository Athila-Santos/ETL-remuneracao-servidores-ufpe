# tests/test_scraper.py

import pytest
import requests
from src.scraper import PortalScraper

# --- 1. Dados Falsos para Simulação (HTML CORRIGIDO) ---

# HTML foi "preenchido" com divs vazias para bater com os XPaths
FAKE_HTML_OK = """
<html>
    <body>
        <div id="collapse-1">
            <div> <div> <div></div> <div> <span class="strong">PROFESSOR DO MAGISTERIO SUPERIOR</span> </div>
                </div>
                <div></div> <div></div> <div> <div> <span class="strong">40 HORAS SEMANAIS</span> </div>
                </div>
                <div></div> <div> <div> <span class="strong">01/01/2010</span> </div>
                </div>
            </div>
        </div>
        <div id="tab-remuneracoesServidor-2-servidor-civil">
            <div>
                <div></div> <div> <div></div> <div> <span class="strong">R$ 10.000,00</span> </div>
                </div>
                <div></div> <div> <div></div> <div> <strong class="strong">R$ 7.500,00</strong> </div>
                </div>
            </div>
        </div>
    </body>
</html>
"""

# HTML Faltando Dado (agora com a estrutura correta, mas o span do 'ingresso' removido)
FAKE_HTML_FALTANDO_DADO = """
<html>
    <body>
        <div id="collapse-1">
            <div> <div> <div></div> <div> <span class="strong">PROFESSOR DO MAGISTERIO SUPERIOR</span> </div>
                </div>
                <div></div> <div></div> <div> <div> <span class="strong">40 HORAS SEMANAIS</span> </div>
                </div>
                <div></div> <div> <div> </div>
                </div>
            </div>
        </div>
        <div id="tab-remuneracoesServidor-2-servidor-civil">
            </div>
    </body>
</html>
"""

# XPaths reais que estamos buscando (copiados do config)
# (Estes devem bater com o seu config.py)
XPATHS_DESC = {
    'classe_cargo': '//*[@id="collapse-1"]/div/div[1]/div[2]/span',
    'jornada': '//*[@id="collapse-1"]/div/div[4]/div[1]/span',
    'ingresso': '//*[@id="collapse-1"]/div/div[6]/div[1]/span'
}
XPATHS_REMUN = {
    'remuneracao_basica_bruta': '//*[@id="tab-remuneracoesServidor-2-servidor-civil"]/div/div[2]/div[2]/span',
    'remuneracao_apos_deducoes': '//*[@id="tab-remuneracoesServidor-2-servidor-civil"]/div/div[4]/div[2]/strong'
}

URL_BASE_TESTE = "http://teste.com"
ID_PORTAL_TESTE = "123456"

# --- 2. Fixture do Scraper ---

@pytest.fixture
def scraper():
    """Retorna uma instância do PortalScraper para os testes."""
    return PortalScraper()

# --- 3. Os Testes (com Mock) ---

def test_extrair_remuneracao_sucesso(scraper, mocker):
    """
    Testa o "caminho feliz": a requisição funciona e todos os dados são encontrados.
    """
    # Arrange (Arrumar)
    mock_response = mocker.Mock()
    mock_response.status_code = 200
    mock_response.content = FAKE_HTML_OK.encode('utf-8') 
    mock_response.raise_for_status.return_value = None 
    
    mock_get = mocker.patch("src.scraper.requests.get", return_value=mock_response)
    
    # Act (Agir)
    resultado = scraper.extrair_remuneracao_servidor(
        id_portal=ID_PORTAL_TESTE,
        url_base=URL_BASE_TESTE,
        xpaths_descricao=XPATHS_DESC,
        xpaths_remuneracao=XPATHS_REMUN
    )
    
    # Assert (Verificar)
    assert resultado is not None
    assert resultado['id_portal'] == ID_PORTAL_TESTE
    assert resultado['classe_cargo'] == "PROFESSOR DO MAGISTERIO SUPERIOR"
    assert resultado['jornada'] == "40 HORAS SEMANAIS"
    assert resultado['ingresso'] == "01/01/2010"
    assert resultado['remuneracao_basica_bruta'] == "R$ 10.000,00"
    assert resultado['remuneracao_apos_deducoes'] == "R$ 7.500,00"
    
    expected_url = f"{URL_BASE_TESTE}/{ID_PORTAL_TESTE}"
    mock_get.assert_called_once_with(
        expected_url, 
        headers=scraper.headers, 
        timeout=15
    )

def test_extrair_remuneracao_falha_http_404(scraper, mocker):
    """
    Testa o "caminho triste": o site retorna um erro 404 (Não Encontrado).
    """
    # Arrange
    # 1. Simule uma resposta com erro 404
    mock_response = mocker.Mock()
    mock_response.status_code = 404
    
    # 2. CRIE O ERRO CORRETAMENTE
    # Crie um erro que TENHA o atributo .response
    http_error = requests.HTTPError("404 Client Error")
    http_error.response = mock_response # <--- A CORREÇÃO ESTÁ AQUI
    
    # 3. Simule o .raise_for_status() levantando esse erro
    mock_response.raise_for_status.side_effect = http_error
    
    # 4. Intercepte o 'requests.get'
    mocker.patch("src.scraper.requests.get", return_value=mock_response)
    
    # Act
    resultado = scraper.extrair_remuneracao_servidor(
        id_portal=ID_PORTAL_TESTE,
        url_base=URL_BASE_TESTE,
        xpaths_descricao=XPATHS_DESC,
        xpaths_remuneracao=XPATHS_REMUN
    )
    
    # Assert
    assert resultado is None

def test_extrair_remuneracao_falha_conexao(scraper, mocker):
    """
    Testa o "caminho triste": a rede falha (ex: sem internet).
    (Este já estava passando, sem mudanças)
    """
    # Arrange
    mocker.patch(
        "src.scraper.requests.get", 
        side_effect=requests.RequestException("Erro de conexão")
    )
    
    # Act
    resultado = scraper.extrair_remuneracao_servidor(
        id_portal=ID_PORTAL_TESTE,
        url_base=URL_BASE_TESTE,
        xpaths_descricao=XPATHS_DESC,
        xpaths_remuneracao=XPATHS_REMUN
    )
    
    # Assert
    assert resultado is None

def test_extrair_remuneracao_dado_faltante(scraper, mocker):
    """
    Testa o "caminho realista": a página carrega, mas um XPath não encontra nada.
    """
    # Arrange
    mock_response = mocker.Mock()
    mock_response.status_code = 200
    mock_response.content = FAKE_HTML_FALTANDO_DADO.encode('utf-8') # <-- HTML Corrigido
    mock_response.raise_for_status.return_value = None
    
    mocker.patch("src.scraper.requests.get", return_value=mock_response)
    
    # Act
    resultado = scraper.extrair_remuneracao_servidor(
        id_portal=ID_PORTAL_TESTE,
        url_base=URL_BASE_TESTE,
        xpaths_descricao=XPATHS_DESC,
        xpaths_remuneracao=XPATHS_REMUN
    )
    
    # Assert
    assert resultado is not None
    assert resultado['jornada'] == "40 HORAS SEMANAIS"
    assert resultado['classe_cargo'] == "PROFESSOR DO MAGISTERIO SUPERIOR"
    assert resultado['ingresso'] is None # <--- Este é o dado que foi removido