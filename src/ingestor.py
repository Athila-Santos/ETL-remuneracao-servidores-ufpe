import requests
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

class IdIngestor:
    """
    Especialista em se conectar à API "escondida" do Portal
    e extrair a lista mestra de IDs de servidores.
    """
    
    def __init__(self, api_url: str, headers: Dict[str, str]):
        if not api_url:
            raise ValueError("URL da API de ingestão não pode ser nula.")
        self.api_url = api_url
        self.headers = headers
        logger.info(f"IdIngestor inicializado para a URL: {api_url}")

    def consultar_dados_api(self) -> List[Dict[str, Any]]:
        """
        Busca e formata os dados da API de consulta.
        
        Returns:
            Uma lista de dicionários (registros) prontos para o Supabase.
        """
        logger.info("Iniciando consulta à API de ingestão de IDs...")
        try:
            response = requests.get(self.api_url, headers=self.headers, timeout=120) # 2 min timeout
            response.raise_for_status() # Lança erro para 4xx/5xx
            
            data = response.json()
            registros = []
            
            if 'data' not in data:
                logger.error("API de ingestão retornou JSON sem a chave 'data'.")
                return []

            for item in data['data']:
                try:
                    # Lógica de parsing do seu script original
                    id_portal = item['idComFlagExisteDetalhamentoServidor'].split("_")[0]
                    
                    registros.append({
                        'id_portal': id_portal,
                        'situacao': item.get('situacao'),
                        'cargo': item.get('cargo'),
                        'funcao': item.get('funcao')
                    })
                except (KeyError, TypeError, AttributeError) as e:
                    logger.warning(f"Erro ao processar item de ingestão: {item}. Erro: {e}")
                    continue
            
            logger.info(f"Ingestão da API concluída. {len(registros)} IDs encontrados.")
            return registros

        except requests.HTTPError as e:
            logger.error(f"Erro HTTP {e.response.status_code} ao buscar API de ingestão.")
            return []
        except requests.RequestException as e:
            logger.error(f"Erro de rede ao buscar API de ingestão: {e}")
            return []
        except Exception as e:
            logger.error(f"Erro inesperado no IdIngestor: {e}")
            return []