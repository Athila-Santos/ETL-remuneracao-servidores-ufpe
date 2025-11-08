import pytest
from src.database import SupabaseClient
from unittest.mock import MagicMock, patch

# --- Testes de __init__ (sem mock) ---

def test_init_falha_com_credenciais_nulas():
    """Testa se o __init__ levanta um ValueError se as chaves não forem dadas."""
    with pytest.raises(ValueError, match="Supabase URL e Key são obrigatórias"):
        SupabaseClient(url=None, key="fake_key")
        
    with pytest.raises(ValueError, match="Supabase URL e Key são obrigatórias"):
        SupabaseClient(url="fake_url", key=None)

# --- Fixture principal para mockar o Supabase ---

@pytest.fixture
def mock_supabase_client(mocker):
    """
    Esta fixture mocka a *biblioteca* 'create_client' dentro do 'src.database'.
    Ela também mocka a instância do cliente que 'create_client' retorna.
    """
    
    # 1. Mocka a *instância* do cliente (o que 'create_client' retorna)
    mock_instance = MagicMock()

    # 2. Mocka a *função* 'create_client' para retornar nossa instância mock
    mock_create = mocker.patch("src.database.create_client", return_value=mock_instance)
    
    # 3. Instancia nossa classe (agora ela receberá o mock)
    #    Nós passamos "fake" aqui só para satisfazer o __init__
    db_client = SupabaseClient(url="fake_url", key="fake_key")
    
    # 4. Retorna as duas coisas para que possamos usá-las nos testes
    return db_client, mock_instance, mock_create


# --- Testes dos Métodos da Classe ---

def test_fetch_ids_para_processar_sucesso(mock_supabase_client):
    """Testa o caminho feliz de buscar IDs."""
    
    # Arrange (Arrumar)
    db_client, mock_instance, _ = mock_supabase_client
    
    # Prepara os dados falsos que a API do Supabase retornaria
    fake_response_data = [
        {'id_portal': '123'},
        {'id_portal': '456'}
    ]
    # Isso simula a cadeia de chamadas:
    # mock_instance.table(...).select(...).eq(...).execute()
    mock_execute = mock_instance.table.return_value.select.return_value.eq.return_value.execute
    mock_execute.return_value.data = fake_response_data
    
    # Act (Agir)
    resultado = db_client.fetch_ids_para_processar(
        tabela_origem="idServidores", 
        coluna="id_portal", 
        filtro_situacao="Ativo"
    )
    
    # Assert (Verificar)
    assert resultado == ['123', '456']
    # Verifica se os métodos corretos foram chamados com os args corretos
    mock_instance.table.assert_called_with("idServidores")
    mock_instance.table.return_value.select.assert_called_with("id_portal")
    mock_instance.table.return_value.select.return_value.eq.assert_called_with("situacao", "Ativo")

def test_fetch_ids_sem_dados(mock_supabase_client):
    """Testa se retorna lista vazia quando o banco não retorna dados."""
    # Arrange
    db_client, mock_instance, _ = mock_supabase_client
    mock_execute = mock_instance.table.return_value.select.return_value.eq.return_value.execute
    mock_execute.return_value.data = [] # <-- A diferença
    
    # Act
    resultado = db_client.fetch_ids_para_processar(
        tabela_origem="tabela_teste", 
        coluna="col_teste", 
        filtro_situacao="filtro_teste"
    )
    
    # Assert
    assert resultado == []

def test_upsert_remuneracao_sucesso(mock_supabase_client):
    """Testa o caminho feliz do upsert."""
    # Arrange
    db_client, mock_instance, _ = mock_supabase_client
    dados_para_salvar = {'id_portal': '123', 'remuneracao': 1000.0}
    
    # Simula a resposta do upsert (deve retornar dados)
    mock_execute = mock_instance.table.return_value.upsert.return_value.execute
    mock_execute.return_value.data = [dados_para_salvar] # <-- Resposta com dados
    
    # Act
    sucesso = db_client.upsert_remuneracao(
        dados=dados_para_salvar,
        tabela_destino="remuneracao",
        coluna_conflito="id_portal"
    )
    
    # Assert
    assert sucesso is True
    mock_instance.table.assert_called_with("remuneracao")
    mock_instance.table.return_value.upsert.assert_called_with(
        dados_para_salvar, 
        on_conflict="id_portal"
    )

def test_upsert_remuneracao_falha(mock_supabase_client):
    """Testa o que acontece se o upsert falhar (levantar exceção)."""
    # Arrange
    db_client, mock_instance, _ = mock_supabase_client
    
    # Simula o .execute() levantando um erro
    mock_execute = mock_instance.table.return_value.upsert.return_value.execute
    mock_execute.side_effect = Exception("Falha no banco de dados")
    
    dados_para_salvar = {'id_portal': '123'}
    
    # Act
    sucesso = db_client.upsert_remuneracao(
        dados=dados_para_salvar,
        tabela_destino="remuneracao",
        coluna_conflito="id_portal"
    )
    
    # Assert
    assert sucesso is False