import logging
from tqdm import tqdm
from .database import SupabaseClient
from .scraper import PortalScraper
from .processing import DataProcessor
from .ingestor import IdIngestor
import config
import time

logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - [%(levelname)s] - [ETLPipeline] - %(message)s'
)
logger = logging.getLogger(__name__)


class ETLPipeline:
    """
    Orquestra o processo de ETL de ponta a ponta.
    Agora inclui o Estágio 1 (Ingestão) e o Estágio 2 (Enriquecimento)
    com a lógica de coleta de variáveis completa para o BI.
    """
    def __init__(self, db_url: str, db_key: str):
        logger.info("Iniciando Pipeline de ETL...")
        try:
            self.db_client = SupabaseClient(db_url, db_key)
            logger.info("Cliente Supabase inicializado.")
        except ValueError as e:
            logger.critical(f"Falha ao inicializar SupabaseClient: {e}")
            raise SystemExit(f"Erro crítico: {e}")
            
        self.scraper = PortalScraper()
        self.processor = DataProcessor()
        self.ingestor = IdIngestor(
            api_url=config.API_URL_INGESTAO, 
            headers=config.API_HEADERS
        )
        
        try:
            # --- BLOCO ATUALIZADO ---
            # Mapeia as novas chaves (que batem com o SQL) 
            # para os XPaths robustos do config.py
            
            # Campos da seção "Vínculo" (section[2])
            self.xpaths_descricao = {
                'cargo_emprego': config.XPATH_CARGO_EMPREGO,
                'classe_cargo': config.XPATH_CLASSE_CARGO,
                'regime_juridico': config.XPATH_REGIME_JURIDICO,
                'jornada': config.XPATH_JORNADA,
                'ingresso_orgao': config.XPATH_INGRESSO_ORGAO,
                'ingresso_servico_publico': config.XPATH_INGRESSO_SERVICO_PUBLICO,
                'forma_ingresso': config.XPATH_FORMA_INGRESSO,
                'afastamento': config.XPATH_AFASTAMENTO,
                'uorg_lotacao': config.XPATH_UORG
            }
            
            # Campos da seção "Remuneração" (section[3])
            self.xpaths_remuneracao = {
                'data_remuneracao': config.XPATH_DATA_REMUNERACAO,
                'remuneracao_basica_bruta': config.XPATH_REMUNERACAO_BASICA,
                'remuneracao_apos_deducoes': config.XPATH_REMUNERACAO_LIQUIDA
            }
            logger.info("Configurações de XPath (v2 Robusta) carregadas.")
            # --- FIM DO BLOCO ATUALIZADO ---

        except AttributeError as e:
            logger.critical(f"Variável de XPath não encontrada no config.py: {e}")
            raise SystemExit(f"Erro de configuração: {e}")

    def _run_stage_1_ingestion(self) -> bool:
        """
        Executa o pipeline de ingestão (Estágio 1).
        Lógica de "Apague e Recarregue".
        """
        logger.warning("Iniciando Estágio 1: Ingestão de IDs (Apague e Recarregue)...")
        
        novos_registros = self.ingestor.consultar_dados_api()
        
        if not novos_registros:
            logger.error("Falha na ingestão: A API não retornou registros.")
            return False
            
        logger.info("Deletando registros antigos da Tabela 1 (idServidores)...")
        sucesso_delete = self.db_client.delete_all_from_table(config.TABELA_IDS)
        
        if not sucesso_delete:
            logger.error("Estágio 1: Falha ao deletar registros antigos. Abortando.")
            return False
            
        logger.info("Inserindo novos registros na Tabela 1 (idServidores)...")
        sucesso_insert = self.db_client.batch_insert_ids(
            registros=novos_registros,
            tabela=config.TABELA_IDS
        )
        
        if sucesso_insert:
            logger.info("Estágio 1: Ingestão 'Apague e Recarregue' concluída.")
        else:
            logger.error("Estágio 1: Falha ao inserir novos registros.")
            
        return sucesso_insert

    def run_etl_remuneracoes(self):
        """
        Executa o pipeline com lógica incremental (DELTA).
        """
        logger.info("--- INICIANDO EXECUÇÃO DO PIPELINE ---")
        
        # === ESTÁGIO 1 (TENTATIVA) ===
        logger.info("Tentando buscar IDs 'Ativos' da tabela fonte...")
        ids_fonte_unicos = self.db_client.fetch_ids_para_processar(
            tabela_origem=config.TABELA_IDS,
            coluna="id_portal",
            filtro_situacao="Ativo"
        )
        
        if not ids_fonte_unicos:
            logger.warning("Nenhum ID 'Ativo' encontrado. Rodando Estágio 1: Ingestão...")
            sucesso_ingestao = self._run_stage_1_ingestion()
            
            if not sucesso_ingestao:
                logger.critical("Falha no Estágio 1. O pipeline não pode continuar.")
                return
            
            logger.info("Tentando buscar IDs 'Ativos' novamente após ingestão...")
            ids_fonte_unicos = self.db_client.fetch_ids_para_processar(
                tabela_origem=config.TABELA_IDS,
                coluna="id_portal",
                filtro_situacao="Ativo"
            )
            
            if not ids_fonte_unicos:
                logger.warning("Ingestão concluída, mas ainda não há IDs 'Ativos'. Encerrando.")
                return

        # === ESTÁGIO 2: LÓGICA INCREMENTAL ===
        logger.info(f"Fonte: Encontrados {len(ids_fonte_unicos)} IDs 'Ativos' únicos.")
        
        ids_ja_processados = self.db_client.fetch_existing_remuneracao_ids(
            config.TABELA_REMUNERACAO
        )

        set_fonte = set(ids_fonte_unicos)
        set_destino = set(ids_ja_processados)
        ids_para_processar = list(set_fonte - set_destino)
        
        logger.info(f"Destino: {len(set_destino)} IDs já processados.")
        logger.info(f"DELTA: {len(ids_para_processar)} novos IDs para raspar.")
        
        if not ids_para_processar:
            logger.info("Nenhum ID novo para processar. Pipeline concluído.")
            return

        # 3. Processa e salva UM POR UM (COM TQDM)
        contador_sucesso = 0
        contador_falha = 0
        
        logger.info("Iniciando Estágio 2: Raspagem de Salários e Vínculos...")
        
        for id_portal in tqdm(ids_para_processar, desc="Raspando Dados (Estágio 2)", unit=" ID"):
            
            dados_brutos = self.scraper.extrair_remuneracao_servidor(
                id_portal=id_portal,
                url_base=config.BASE_URL_SERVIDORES,
                xpaths_descricao=self.xpaths_descricao,
                xpaths_remuneracao=self.xpaths_remuneracao
            )
            
            if dados_brutos is None:
                logger.warning(f"Falha ao raspar dados para o ID: {id_portal}. Pulando.")
                contador_falha += 1
                continue
            
            try:
                # O Processor agora formata os novos campos
                dados_limpos = self.processor.formatar_dados_servidor(dados_brutos)
            except Exception as e:
                logger.error(f"Erro ao formatar dados para o ID {id_portal}: {e}")
                contador_falha += 1
                continue

            # O DatabaseClient agora salva o dicionário maior
            sucesso_upsert = self.db_client.upsert_remuneracao(
                dados=dados_limpos,
                tabela_destino=config.TABELA_REMUNERACAO,
                coluna_conflito='id_portal'
            )
            
            if sucesso_upsert:
                contador_sucesso += 1
            else:
                logger.error(f"Falha ao salvar dados no Supabase para o ID {id_portal}.")
                contador_falha += 1

            time.sleep(0.5)
            
        # === RESUMO FINAL ===
        logger.info("--- RESUMO DO ESTÁGIO 2 (INCREMENTAL) ---")
        logger.info(f"Total de novos IDs processados: {len(ids_para_processar)}")
        logger.info(f"Registros salvos com sucesso: {contador_sucesso}")
        logger.info(f"Falhas/Pulados: {contador_falha}")
        logger.info("--- PIPELINE COMPLETO CONCLUÍDO ---")