import requests
import logging
from typing import List, Dict, Any, Optional
from collections import defaultdict

logger = logging.getLogger(__name__)

class IdIngestor:
    """
    Especialista em se conectar à API "escondida" do Portal
    e extrair a lista mestra de IDs de servidores.
    
    AGORA TAMBÉM AGREGA os registros duplicados antes de retornar.
    """
    
    def __init__(self, api_url: str, headers: Dict[str, str]):
        if not api_url:
            raise ValueError("URL da API de ingestão não pode ser nula.")
        self.api_url = api_url
        self.headers = headers
        logger.info(f"IdIngestor inicializado para a URL: {api_url}")

    def _agregar_registros(self, registros: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Aplica a lógica de negócio de agregação de registros duplicados.
        (Sua otimização!)
        """
        logger.info(f"Agregando {len(registros)} registros brutos...")
        
        # 1. Agrupa todos os registros por 'id_portal'
        registros_agrupados = defaultdict(list)
        for r in registros:
            registros_agrupados[r['id_portal']].append(r)
            
        lista_agregada = []
        
        # 2. Itera sobre cada grupo de IDs
        for id_portal, items in registros_agrupados.items():
            if len(items) == 1:
                # Se só tem um, não há o que agregar
                lista_agregada.append(items[0])
                continue
            
            # Se tem múltiplos (ex: Cargo e Função separados)
            # 1. Encontra o registro "principal" (o que tem o Cargo)
            #    Usamos 'items[0]' como fallback se nenhum tiver cargo.
            principal = next((r for r in items if "Sem informaç" not in r.get('cargo', 'Sem informaç')), items[0])
            
            # 2. Encontra o registro que tem a "Função" (se existir)
            funcao = next((r['funcao'] for r in items if "Sem função" not in r.get('funcao', 'Sem função')), None)
            
            # 3. Agrega: Sobrescreve a 'funcao' do registro principal
            if funcao:
                principal['funcao'] = funcao
                
            # 4. (Opcional) Agrega a situação mais "ativa"
            principal['situacao'] = next((r['situacao'] for r in items if r.get('situacao') == 'Ativo'), principal['situacao'])

            lista_agregada.append(principal)
            
        logger.info(f"Agregação concluída. {len(lista_agregada)} registros únicos/agregados.")
        return lista_agregada


    def consultar_dados_api(self) -> List[Dict[str, Any]]:
        """
        Busca e formata os dados da API de consulta.
        """
        logger.info("Iniciando consulta à API de ingestão de IDs...")
        try:
            response = requests.get(self.api_url, headers=self.headers, timeout=120)
            response.raise_for_status()
            
            data = response.json()
            registros_brutos = []
            
            if 'data' not in data:
                logger.error("API de ingestão retornou JSON sem a chave 'data'.")
                return []

            for item in data['data']:
                try:
                    id_portal = item['idComFlagExisteDetalhamentoServidor'].split("_")[0]
                    
                    registros_brutos.append({
                        'id_portal': id_portal,
                        'situacao': item.get('situacao'),
                        'cargo': item.get('cargo'),
                        'funcao': item.get('funcao')
                    })
                except (KeyError, TypeError, AttributeError) as e:
                    logger.warning(f"Erro ao processar item de ingestão: {item}. Erro: {e}")
                    continue
            
            logger.info(f"Ingestão da API concluída. {len(registros_brutos)} registros brutos encontrados.")
            
            registros_agregados = self._agregar_registros(registros_brutos)
            
            return registros_agregados

        except requests.HTTPError as e:
            logger.error(f"Erro HTTP {e.response.status_code} ao buscar API de ingestão.")
            return []
        except requests.RequestException as e:
            logger.error(f"Erro de rede ao buscar API de ingestão: {e}")
            return []
        except Exception as e:
            logger.error(f"Erro inesperado no IdIngestor: {e}")
            return []