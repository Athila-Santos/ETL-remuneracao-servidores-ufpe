import sys
import logging
from src.pipeline import ETLPipeline
import config

logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - [%(levelname)s] - %(name)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

def run_pipeline():
    """
    Função principal para inicializar e executar o pipeline de ETL.
    """
    logger.info("==============================================")
    logger.info("=== INICIANDO PIPELINE DE ETL - PORTAL DA TRANSPARÊNCIA ===")
    logger.info("==============================================")

    try:
        # 1. Valida se as configurações essenciais foram carregadas
        if not config.SUPABASE_URL or not config.SUPABASE_KEY:
            logger.critical("SUPABASE_URL ou SUPABASE_KEY não encontradas no .env.")
            logger.critical("Por favor, verifique seu arquivo .env.")
            return

        # 2. Cria a instância do "Gerente" (Pipeline)
        pipeline = ETLPipeline(
            db_url=config.SUPABASE_URL,
            db_key=config.SUPABASE_KEY
        )
        
        # 3. Dá o comando para o Gerente "começar o trabalho"
        pipeline.run_etl_remuneracoes()

    except SystemExit as e:
        logger.error(f"Execução interrompida: {e}")
    except Exception as e:
        logger.critical(f"Ocorreu um erro fatal e inesperado no pipeline: {e}", exc_info=True)
    finally:
        logger.info("==============================================")
        logger.info("=== EXECUÇÃO DO PIPELINE FINALIZADA ===")
        logger.info("==============================================")


if __name__ == "__main__":
    """
    Este é o ponto de entrada padrão em Python.
    O código aqui dentro só roda quando você executa: python main.py
    """
    run_pipeline()