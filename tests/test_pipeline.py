import pytest
from src.pipeline import ETLPipeline
import config
from unittest.mock import MagicMock, patch

# --- Fixture principal para mockar TODAS as dependências ---

@pytest.fixture
def setup_pipeline(mocker):
    """
    Mocka todas as classes que o ETLPipeline importa e usa.
    """
    # 1. Mocka as classes "Especialistas"
    mock_db_class = mocker.patch("src.pipeline.SupabaseClient")
    mock_scraper_class = mocker.patch("src.pipeline.PortalScraper")
    mock_processor_class = mocker.patch("src.pipeline.DataProcessor")
    
    # 2. Mocka as *instâncias* que o __init__ do pipeline irá criar
    mock_db_instance = MagicMock()
    mock_scraper_instance = MagicMock()
    mock_processor_instance = MagicMock()
    
    # 3. Diz às classes mockadas para retornarem nossas instâncias mock
    mock_db_class.return_value = mock_db_instance
    mock_scraper_class.return_value = mock_scraper_instance
    mock_processor_class.return_value = mock_processor_instance
    
    # 4. Mocka o config para evitar erros de AttributeError se XPaths mudarem
    mocker.patch.object(config, 'XPATH_CLASSE_CARGO', 'xpath_cargo')
    mocker.patch.object(config, 'XPATH_JORNADA', 'xpath_jornada')
    mocker.patch.object(config, 'XPATH_INGRESSO', 'xpath_ingresso')
    mocker.patch.object(config, 'XPATH_REMUNERACAO_BASICA', 'xpath_basica')
    mocker.patch.object(config, 'XPATH_REMUNERACAO_LIQUIDA', 'xpath_liquida')
    
    # 5. Finalmente, cria a instância do Pipeline (agora 100% mockado)
    pipeline = ETLPipeline(db_url="fake_url", db_key="fake_key")
    
    # 6. Retorna tudo que os testes precisam
    return pipeline, mock_db_instance, mock_scraper_instance, mock_processor_instance


# --- Testes dos Métodos do Pipeline ---

def test_pipeline_caminho_feliz(setup_pipeline):
    """Testa o caminho perfeito: 2 IDs, 2 scrapes, 2 processamentos, 2 upserts."""
    
    # Arrange (Arrumar)
    pipeline, db, scraper, processor = setup_pipeline
    
    # Simula o banco retornando 2 IDs
    db.fetch_ids_para_processar.return_value = ['123', '456']
    
    # Simula o scraper retornando dados
    scraper.extrair_remuneracao_servidor.side_effect = [
        {'id_portal': '123', 'ingresso': '01/01/2020'}, # Resultado para '123'
        {'id_portal': '456', 'ingresso': '02/02/2020'}  # Resultado para '456'
    ]
    
    # Simula o processor retornando dados limpos
    processor.formatar_dados_servidor.side_effect = [
        {'id_portal': '123', 'ingresso': '2020-01-01'}, # Resultado para '123'
        {'id_portal': '456', 'ingresso': '2020-02-02'}  # Resultado para '456'
    ]
    
    # Simula o upsert sendo bem sucedido
    db.upsert_remuneracao.return_value = True

    # Act (Agir)
    pipeline.run_etl_remuneracoes()

    # Assert (Verificar)
    # Garante que o fetch foi chamado
    db.fetch_ids_para_processar.assert_called_once()
    
    # Garante que o scraper, processor e upsert foram chamados 2 vezes
    assert scraper.extrair_remuneracao_servidor.call_count == 2
    assert processor.formatar_dados_servidor.call_count == 2
    assert db.upsert_remuneracao.call_count == 2

def test_pipeline_sem_ids(setup_pipeline):
    """Testa o que acontece se o banco não retornar nenhum ID."""
    
    # Arrange
    pipeline, db, scraper, processor = setup_pipeline
    db.fetch_ids_para_processar.return_value = [] # <-- A diferença
    
    # Act
    pipeline.run_etl_remuneracoes()
    
    # Assert
    # Garante que, se não há IDs, o resto do pipeline NUNCA é chamado
    db.fetch_ids_para_processar.assert_called_once()
    scraper.extrair_remuneracao_servidor.assert_not_called()
    processor.formatar_dados_servidor.assert_not_called()
    db.upsert_remuneracao.assert_not_called()

def test_pipeline_falha_no_scraper(setup_pipeline):
    """Testa se o scraper falhar (retornar None), o processor e o upsert não são chamados."""
    
    # Arrange
    pipeline, db, scraper, processor = setup_pipeline
    db.fetch_ids_para_processar.return_value = ['123']
    scraper.extrair_remuneracao_servidor.return_value = None # <-- Scraper falhou
    
    # Act
    pipeline.run_etl_remuneracoes()
    
    # Assert
    scraper.extrair_remuneracao_servidor.assert_called_once()
    # Garante que o pipeline "parou" ali para aquele ID
    processor.formatar_dados_servidor.assert_not_called()
    db.upsert_remuneracao.assert_not_called()

def test_pipeline_falha_no_processor(setup_pipeline):
    """Testa se o processor falhar (levantar exceção), o upsert não é chamado."""
    
    # Arrange
    pipeline, db, scraper, processor = setup_pipeline
    db.fetch_ids_para_processar.return_value = ['123']
    scraper.extrair_remuneracao_servidor.return_value = {'id_portal': '123'} # Scraper OK
    processor.formatar_dados_servidor.side_effect = Exception("Erro de formatação") # <-- Processor falhou
    
    # Act
    pipeline.run_etl_remuneracoes()
    
    # Assert
    scraper.extrair_remuneracao_servidor.assert_called_once()
    processor.formatar_dados_servidor.assert_called_once()
    # Garante que o pipeline "parou" ali
    db.upsert_remuneracao.assert_not_called()