from extract_pagamentoServidores import *
import pandas as pd
import requests
from lxml import html
from time import sleep
from supabase import create_client, Client
from dotenv import load_dotenv
import os

# Carregar variáveis de ambiente do arquivo .env
load_dotenv()

# Obter URL e chave do Supabase das variáveis de ambiente
url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")

supabase: Client = create_client(url, key)

tabela = "idServidores"
coluna = "id_portal"

# Execute a consulta com filtro adicional
response = supabase.table(tabela).select(coluna).eq('situacao','Ativo').execute()

ids_supabase = list(response)[0][1]
listaId = []

for i in range(0, len(ids_supabase)):

    listaId.append(ids_supabase[i]['id_portal'])


for i in range(0, len(listaId)):

    dados_funcionario_ativo = extrair_remuneracao_servidor(listaId[i])

    dados_tratados = aplicar_formatacao(dados_funcionario_ativo)
    print(dados_tratados)
    try:
        response = supabase.table('remuneracaoServidoresAtivos').insert(dados_tratados).execute()
        print(response)
    except Exception as e:
        print(e)

# parou em 1810792