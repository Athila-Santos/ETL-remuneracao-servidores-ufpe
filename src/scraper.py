import requests
import logging
from lxml import html
from time import sleep
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class PortalScraper:
    """
    Especialista em se comunicar e extrair dados do Portal da Transparência.
    """
    
    def __init__(self, user_agent: str = None):
        """
        Inicializa o scraper, definindo os headers HTTP.
        """
        self.headers = {
            'User-Agent': user_agent or (
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                '(KHTML, like Gecko) Chrome/90.0.4430.93 Safari/537.36'
            )
        }
        logger.info("PortalScraper inicializado.")

    def extrair_remuneracao_servidor(
        self, 
        id_portal: str, 
        url_base: str, 
        xpaths_descricao: Dict[str, str], 
        xpaths_remuneracao: Dict[str, str]
    ) -> Optional[Dict[str, Any]]:
        """
        Extrai os dados de remuneração e descrição para um único servidor.

        Args:
            id_portal: O ID do servidor no portal.
            url_base: A URL base (ex: 'https://.../servidores').
            xpaths_descricao: Dicionário {'nome_campo': 'xpath'} para dados de descrição.
            xpaths_remuneracao: Dicionário {'nome_campo': 'xpath'} para dados de remuneração.

        Returns:
            Um dicionário com os dados extraídos ou None em caso de falha.
        """
        url = f'{url_base}/{id_portal}'
        dados_servidor = {'id_portal': id_portal}

        try:
            # Adicionamos 'timeout' como boa prática
            response = requests.get(url, headers=self.headers, timeout=15)
            
            # Lança um erro se a resposta não for 200 OK
            response.raise_for_status()
            
            tree = html.fromstring(response.content)

            # --- 1. Extrai dados de DESCRIÇÃO (lógica simples) ---
            for chave, xpath in xpaths_descricao.items():
                element = tree.xpath(xpath)
                if element:
                    dados_servidor[chave] = element[0].text.strip() if element[0].text else None
                else:
                    logger.warning(f"XPath para '{chave}' não encontrado no ID {id_portal}")
                    dados_servidor[chave] = None
            
            # --- 2. Extrai dados de REMUNERAÇÃO (lógica complexa original) ---
            # Esta é a sua lógica que procura por XPaths alternativos
            for chave, xpath_base in xpaths_remuneracao.items():
                element = tree.xpath(xpath_base)
                
                if element:
                    # Encontrou de primeira
                    dados_servidor[chave] = element[0].text.strip() if element[0].text else None
                else:
                    # Não encontrou? Tenta a lógica de substituição
                    found = False
                    # Esta lógica de "replace('4', str(i))" é frágil,
                    # mas estou mantendo-a exatamente como no seu original.
                    for i in range(4, 9): 
                        try:
                            modified_xpath = xpath_base.replace('4', str(i))
                            element = tree.xpath(modified_xpath)
                            if element:
                                dados_servidor[chave] = element[0].text.strip() if element[0].text else None
                                found = True
                                break
                        except Exception as e:
                            # Ignora erro no Xpath modificado
                            logger.debug(f"Erro ao tentar XPath modificado {modified_xpath}: {e}")
                            continue
                    
                    if not found:
                        logger.warning(f"XPath para '{chave}' (nem alternativos) não encontrado no ID {id_portal}")
                        dados_servidor[chave] = None

            return dados_servidor

        except requests.HTTPError as e:
            # Erros como 404 (Não Encontrado) ou 403 (Proibido)
            logger.error(f"Erro HTTP {e.response.status_code} ao buscar ID {id_portal} na URL: {url}")
            return None
        except requests.RequestException as e:
            # Erros de rede, DNS, timeout, etc.
            logger.error(f"Erro de rede ao buscar ID {id_portal}: {e}")
            # Mantém a lógica original de esperar antes de continuar
            sleep(20) 
            return None
        except Exception as e:
            # Pega qualquer outro erro inesperado (ex: parsing do lxml)
            logger.critical(f"Erro inesperado ao processar ID {id_portal}: {e}")
            return None