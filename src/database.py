import logging
from supabase import create_client, Client
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

class SupabaseClient:
    """
    Gerencia todas as interações com o banco de dados Supabase.
    """

    def __init__(self, url: str, key: str):
        """
        Inicializa o cliente Supabase.
        
        Args:
            url: A URL do projeto Supabase.
            key: A chave de API (anon/public ou service_role).
        """
        if not url or not key:
            logger.critical("URL ou Key do Supabase não fornecidas.")
            raise ValueError("Supabase URL e Key são obrigatórias.")
            
        try:
            self.supabase: Client = create_client(url, key)
            logger.info("Cliente Supabase inicializado com sucesso.")
        except Exception as e:
            logger.critical(f"Falha ao criar cliente Supabase: {e}")
            raise

    def fetch_ids_para_processar(
        self, 
        tabela_origem: str, 
        coluna: str = "id_portal", 
        filtro_situacao: str = 'Ativo'
    ) -> List[str]:
        """
        Busca uma lista de IDs na tabela especificada, filtrando por situação.

        Args:
            tabela_origem: Nome da tabela para buscar os IDs (ex: 'idServidores').
            coluna: Nome da coluna que contém o ID (ex: 'id_portal').
            filtro_situacao: Valor para filtrar a coluna 'situacao' (padrão: 'Ativo').

        Returns:
            Uma lista de strings contendo os IDs encontrados.
        """
        try:
            logger.info(f"Buscando IDs na tabela '{tabela_origem}' com situação '{filtro_situacao}'...")
            
            response = self.supabase.table(tabela_origem)\
                                   .select(coluna)\
                                   .eq('situacao', filtro_situacao)\
                                   .execute()
            
            # A resposta do supabase-py vem em response.data
            dados = response.data
            
            if not dados:
                logger.warning(f"Nenhum registro encontrado na tabela '{tabela_origem}' com o filtro especificado.")
                return []
                
            # Extrai os valores da coluna desejada (com duplicatas)
            ids_com_duplicatas = [item[coluna] for item in dados if coluna in item]
            
            # Converte para um set (que remove duplicatas) e de volta para list
            ids_unicos = list(set(ids_com_duplicatas))
            
            logger.info(f"Encontrados {len(ids_com_duplicatas)} registros 'Ativos', "
                        f"resultando em {len(ids_unicos)} IDs únicos para processar.")
            
            return ids_unicos

        except Exception as e:
            logger.error(f"Erro ao buscar IDs do Supabase na tabela '{tabela_origem}': {e}")
            # Em caso de erro, retorna lista vazia para não quebrar o pipeline
            return []

    def batch_insert_remuneracoes(self, registros: List[Dict[str, Any]], tabela: str) -> bool:
        """
        Faz um INSERT em LOTE de múltiplos registros na tabela de remuneração.
        """
        if not registros:
            logger.warning("Nenhum registro de remuneração fornecido para batch_insert.")
            return False
        
        logger.info(f"Iniciando batch insert de {len(registros)} registros de remuneração...")
        try:
            # .insert() aceita uma lista de dicionários
            response = self.supabase.table(tabela).insert(registros).execute()
            
            if response.data:
                logger.info("Batch insert de remuneração concluído com sucesso.")
                return True
            else:
                logger.warning(f"Batch insert de remuneração executado, mas sem dados retornados.")
                return False
        except Exception as e:
            logger.error(f"Erro fatal durante o batch insert de remuneração: {e}")
            return False
        
    def delete_all_from_table(self, tabela: str) -> bool:
        """
        Deleta TODOS os registros de uma tabela. CUIDADO.
        """
        logger.warning(f"Iniciando DELETE total de registros da tabela '{tabela}'...")
        try:
            # .delete() com .neq() em uma coluna que sempre existe (ex: id_portal)
            # é uma forma de deletar tudo
            response = self.supabase.table(tabela).delete().neq('id_portal', 'valor_impossivel').execute()
            
            logger.info(f"Registros da tabela '{tabela}' deletados com sucesso.")
            return True
        except Exception as e:
            logger.error(f"Erro ao deletar registros da tabela '{tabela}': {e}")
            return False

    def batch_insert_ids(self, registros: List[Dict[str, Any]], tabela: str) -> bool:
        """
        Faz um INSERT em LOTE de múltiplos registros na tabela de IDs.
        (Versão modificada do 'upsert' para ser um 'insert' simples)
        """
        if not registros:
            logger.warning("Nenhum registro fornecido para batch_insert_ids.")
            return False
        
        logger.info(f"Iniciando batch insert de {len(registros)} registros para a tabela '{tabela}'...")
        try:
            # MUDANÇA: .upsert() virou .insert()
            response = self.supabase.table(tabela)\
                                   .insert(registros)\
                                   .execute()
            
            if response.data:
                logger.info("Batch insert concluído com sucesso.")
                return True
            else:
                logger.warning(f"Batch insert executado, mas sem dados retornados.")
                return False
        except Exception as e:
            logger.error(f"Erro fatal durante o batch insert: {e}")
            return False
    
    def fetch_existing_remuneracao_ids(self, tabela: str) -> List[str]:
        """
        Busca todos os 'id_portal' que JÁ EXISTEM na tabela de remuneração.
        """
        logger.info(f"Buscando IDs existentes na tabela de destino '{tabela}'...")
        try:
            response = self.supabase.table(tabela).select('id_portal').execute()
            dados = response.data
            
            if not dados:
                logger.info("Nenhum ID existente encontrado na tabela de destino.")
                return []
                
            ids_existentes = list(set(item['id_portal'] for item in dados if 'id_portal' in item))
            logger.info(f"Encontrados {len(ids_existentes)} IDs já processados.")
            return ids_existentes

        except Exception as e:
            logger.error(f"Erro ao buscar IDs existentes: {e}")
            return []
        
    def upsert_remuneracao(
        self, 
        dados: Dict[str, Any], 
        tabela_destino: str,
        coluna_conflito: str = 'id_portal'
    ) -> bool:
        """
        Insere ou atualiza (Upsert) um ÚNICO registro de remuneração.
        (Usado pelo pipeline incremental no Estágio 2).
        """
        try:
            # .upsert() com on_conflict (agora vai funcionar 
            # pois a Tabela 2 tem a restrição UNIQUE)
            response = self.supabase.table(tabela_destino)\
                                   .upsert(dados, on_conflict=coluna_conflito)\
                                   .execute()
            
            if response.data:
                logger.debug(f"Upsert bem-sucedido para {coluna_conflito}: {dados.get(coluna_conflito)}")
                return True
            else:
                logger.warning(f"Upsert completado, mas sem dados retornados para {dados.get(coluna_conflito)}")
                return True

        except Exception as e:
            logger.error(f"Erro ao realizar upsert na tabela '{tabela_destino}' para {dados.get(coluna_conflito)}: {e}")
            return False