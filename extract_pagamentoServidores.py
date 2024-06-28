import pandas as pd
import requests
from lxml import html
from time import sleep
from supabase import create_client, Client
from dotenv import load_dotenv
import os

def extrair_remuneracao_servidor(id_portal):
    # Headers para simular uma requisição de navegador
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                      '(KHTML, like Gecko) Chrome/90.0.4430.93 Safari/537.36'
    }

    # XPath para cada informação desejada
    xpath_expressions = {
        'classe_cargo': '//*[@id="collapse-1"]/div/div[1]/div[2]/span',
        'jornada': '//*[@id="collapse-1"]/div/div[4]/div[1]/span',
        'ingresso': '//*[@id="collapse-1"]/div/div[6]/div[1]/span',
        'remuneracao_basica_bruta': '//*[@id="tab-remuneracoesServidor-2-servidor-civil"]/div/div[2]/div[2]/span',
        'remuneracao_apos_deducoes': '//*[@id="tab-remuneracoesServidor-2-servidor-civil"]/div/div[4]/div[2]/strong'
    }
    url = f'https://portaldatransparencia.gov.br/servidores/{id_portal}'

    try:
        # Realiza a requisição GET com os headers definidos
        response = requests.get(url, headers=headers)

        # Verifica se a requisição foi bem-sucedida
        if response.status_code == 200:
            # Parseia o conteúdo HTML usando lxml
            tree = html.fromstring(response.content)

            # Dicionário para armazenar as informações do servidor
            dados_servidor = {}

            # Extrai as informações usando os XPaths definidos
            for chave, xpath_expression in xpath_expressions.items():
                dados_servidor['id_portal'] = id_portal
                # Tenta encontrar o elemento com o XPath especificado
                element = tree.xpath(xpath_expression)

                # Verifica se o elemento foi encontrado
                if element:
                    dados_servidor[chave] = element[0].text.strip()
                else:
                    dados_servidor[chave] = None

            return dados_servidor

        else:
            print(f"Erro na requisição: {response.status_code}")

    except requests.RequestException as e:
        print(f"Erro na requisição: {str(e)}")

        # Aguarda 20 segundos antes de tentar novamente
        sleep(20)

    # Se todas as tentativas falharem, retorna None
    return None

def formatar_valor(valor_str):
    """
    Formata um valor monetário representado como string para float.
    Remove pontos, espaços e substitui vírgulas por pontos.
    """
    print(type(valor_str))
    if isinstance(valor_str, str):
        valor_str = valor_str.replace('.', '').replace(',', '.').replace(" ", "")
        return float(valor_str)
    else:
        raise ValueError("O valor a ser formatado deve ser uma string.")

def formatar_data(data_str):
    """
    Formata uma data representada como string para o formato 'YYYY-MM-DD'.
    """
    try:
        data_obj = pd.to_datetime(data_str, format='%d/%m/%Y').date()
        return data_obj.strftime('%Y-%m-%d')
    except ValueError:
        raise ValueError(f"A data '{data_str}' não está no formato esperado '%d/%m/%Y'.")

def aplicar_formatacao(dados_servidor):
    try:
        dados_servidor['ingresso'] = formatar_data(dados_servidor['ingresso'])
        dados_servidor['remuneracao_basica_bruta'] = formatar_valor(dados_servidor['remuneracao_basica_bruta'])
        dados_servidor['remuneracao_apos_deducoes'] = formatar_valor(dados_servidor['remuneracao_apos_deducoes'])
    except ValueError as e:
        print(f"Erro ao formatar dados: {str(e)}")
    return dados_servidor