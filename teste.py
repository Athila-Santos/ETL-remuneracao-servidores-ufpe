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
coluna = ("id_portal,situacao")

# Execute a consulta com filtro adicional
response = supabase.table(tabela).select(coluna).execute()

ids_supabase = list(response)[0][1]

listaId = []

for item in ids_supabase:
    listaId.append({'id_portal': item['id_portal'], 'situacao': item['situacao']})

# Referenciar os itens da sublista
primeiro_item = listaId[9]  # Primeiro dicionário na lista

id_portal = primeiro_item['id_portal']
situacao = primeiro_item['situacao']

print(f"ID Portal: {id_portal}, Situação: {situacao}")

'''
tem que ter uma validação

se for pensionista, aposentado ou ativo seguirá um caminho distinto

caso algum retorno dê nulo, testar outras hipoteses



'''