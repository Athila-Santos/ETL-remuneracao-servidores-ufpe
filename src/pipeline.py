import logging
from tqdm import tqdm
from .database import SupabaseClient
from .scraper import PortalScraper
from .processing import DataProcessor
from .ingestor import IdIngestor
import config

logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - [%(levelname)s] - [ETLPipeline] - %(message)s'
)
logger = logging.getLogger(__name__)


class ETLPipeline:
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
            self.xpaths_descricao = {
                'classe_cargo': config.XPATH_CLASSE_CARGO,
                'jornada': config.XPATH_JORNADA,
                'ingresso': config.XPATH_INGRESSO
            }
            self.xpaths_remuneracao = {
                'remuneracao_basica_bruta': config.XPATH_REMUNERACAO_BASICA,
                'remuneracao_apos_deducoes': config.XPATH_REMUNERACAO_LIQUIDA
            }
        except AttributeError as e:
            logger.critical(f"Variável de XPath não encontrada no config.py: {e}")
            raise SystemExit(f"Erro de configuração: {e}")

    def _run_stage_1_ingestion(self) -> bool:
        """
        Executa o pipeline de ingestão (Estágio 1).
        Lógica de "Apague e Recarregue".
        """
        logger.warning("Iniciando Estágio 1: Ingestão de IDs (Apague e Recarregue)...")
        
        # 1. Coleta dados da API (em memória)
        novos_registros = self.ingestor.consultar_dados_api()
        
        if not novos_registros:
            logger.error("Falha na ingestão: A API não retornou registros.")
            return False
            
        # 2. APAGA os dados antigos da tabela
        sucesso_delete = self.db_client.delete_all_from_table(config.TABELA_IDS)
        
        if not sucesso_delete:
            logger.error("Estágio 1: Falha ao deletar registros antigos. Abortando.")
            return False
            
        # 3. INSERE os novos dados
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
        Estágio 1: Garante que os IDs fonte existem.
        Estágio 2: Calcula o delta e processa apenas os novos IDs com uma barra de progresso.
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
        
        # --- AQUI ESTÁ A MUDANÇA ---
        # Envolvemos 'ids_para_processar' com o 'tqdm'
        # 'desc' = Título da barra
        # 'unit' = O que estamos contando (IDs)
        logger.info("Iniciando Estágio 2: Raspagem de Salários...")
        
        for id_portal in tqdm(ids_para_processar, desc="Raspando Salários (Estágio 2)", unit=" ID"):
            
            # Não precisamos mais disso, o tqdm já mostra o progresso:
            # logger.info(f"Processando novo ID: {id_portal}...") 
            
            dados_brutos = self.scraper.extrair_remuneracao_servidor(
                id_portal=id_portal,
                url_base=config.BASE_URL_SERVIDORES,
                xpaths_descricao=self.xpaths_descricao,
                xpaths_remuneracao=self.xpaths_remuneracao
            )
            
            if dados_brutos is None:
                # O logger.warning ainda é ótimo, o tqdm vai imprimi-lo
                # acima da barra de progresso sem quebrá-la.
                logger.warning(f"Falha ao raspar dados para o ID: {id_portal}. Pulando.")
                contador_falha += 1
                continue
            
            try:
                dados_limpos = self.processor.formatar_dados_servidor(dados_brutos)
            except Exception as e:
                logger.error(f"Erro ao formatar dados para o ID {id_portal}: {e}")
                contador_falha += 1
                continue

            sucesso_upsert = self.db_client.upsert_remuneracao(
                dados=dados_limpos,
                tabela_destino=config.TABELA_REMUNERACAO,
                coluna_conflito='id_portal'
            )
            
            if sucesso_upsert:
                # Este log também é desnecessário, podemos silenciá-lo
                # logger.info(f"Dados para o ID {id_portal} salvos com sucesso.")
                contador_sucesso += 1
            else:
                logger.error(f"Falha ao salvar dados no Supabase para o ID {id_portal}.")
                contador_falha += 1
        
        # O 'tqdm' automaticamente imprime o tempo total quando o loop acaba.

        # === RESUMO FINAL ===
        logger.info("--- RESUMO DO ESTÁGIO 2 (INCREMENTAL) ---")
        logger.info(f"Total de novos IDs processados: {len(ids_para_processar)}")
        logger.info(f"Registros salvos com sucesso: {contador_sucesso}")
        logger.info(f"Falhas/Pulados: {contador_falha}")
        logger.info("--- PIPELINE COMPLETO CONCLUÍDO ---")