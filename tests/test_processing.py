import pytest
from src.processing import DataProcessor

# 1. "Fixture": Um setup que o pytest pode reutilizar.
#    Isso cria uma instância do DataProcessor uma vez
#    e a "injeta" em qualquer teste que a pedir.
@pytest.fixture
def processor():
    """Retorna uma instância do DataProcessor para os testes."""
    return DataProcessor()


# --- Testes para o método _formatar_valor_monetario ---

def test_formatar_valor_monetario_valido(processor):
    # Arrange (Arrumar)
    valor_sujo = "R$ 1.234,56"
    valor_esperado = 1234.56
    
    # Act (Agir)
    resultado = processor._formatar_valor_monetario(valor_sujo)
    
    # Assert (Verificar)
    assert resultado == valor_esperado

def test_formatar_valor_monetario_com_espacos(processor):
    # Arrange
    valor_sujo = " 500,00 "
    valor_esperado = 500.00
    
    # Act
    resultado = processor._formatar_valor_monetario(valor_sujo)
    
    # Assert
    assert resultado == valor_esperado

def test_formatar_valor_monetario_none(processor):
    # Arrange
    valor_sujo = None
    valor_esperado = None
    
    # Act
    resultado = processor._formatar_valor_monetario(valor_sujo)
    
    # Assert
    assert resultado == valor_esperado

def test_formatar_valor_monetario_invalido(processor):
    # Arrange
    valor_sujo = "abc"
    valor_esperado = None
    
    # Act
    resultado = processor._formatar_valor_monetario(valor_sujo)
    
    # Assert
    assert resultado == valor_esperado


# --- Testes para o método _formatar_data ---

def test_formatar_data_valida(processor):
    # Arrange
    data_suja = "25/12/2024"
    data_esperada = "2024-12-25"
    
    # Act
    resultado = processor._formatar_data(data_suja)
    
    # Assert
    assert resultado == data_esperada

def test_formatar_data_invalida(processor):
    # Arrange
    data_suja = "30/02/2024" # Data não existe
    data_esperada = None
    
    # Act
    resultado = processor._formatar_data(data_suja)
    
    # Assert
    assert resultado == data_esperada

def test_formatar_data_formato_errado(processor):
    # Arrange
    data_suja = "2024-12-25" # Formato ISO, não o esperado
    data_esperada = None
    
    # Act
    resultado = processor._formatar_data(data_suja)
    
    # Assert
    assert resultado == data_esperada


# --- Teste para o método principal formatar_dados_servidor ---

def test_formatar_dados_servidor_completo(processor):
    # Arrange
    dados_brutos = {
        'id_portal': '123',
        'classe_cargo': 'PROFESSOR',
        'ingresso': '01/03/2010',
        'remuneracao_basica_bruta': '10.000,00',
        'remuneracao_apos_deducoes': ' 7.500,50 '
    }
    
    dados_esperados = {
        'id_portal': '123',
        'classe_cargo': 'PROFESSOR',
        'ingresso': '2010-03-01',
        'remuneracao_basica_bruta': 10000.00,
        'remuneracao_apos_deducoes': 7500.50
    }
    
    # Act
    resultado = processor.formatar_dados_servidor(dados_brutos)
    
    # Assert
    assert resultado == dados_esperados