from supabase import create_client, Client
from dotenv import load_dotenv
import os
from collections import defaultdict

# Carregar variáveis de ambiente do arquivo .env
load_dotenv()

# Obter URL e chave do Supabase das variáveis de ambiente
url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(url, key)

# Obtém todos os registros da tabela
response = supabase.table('idServidores_2').select('*').execute()
dados = response.data

# Verifica se dados foram obtidos corretamente
if not dados:
    print("Nenhum dado foi encontrado na tabela.")
    exit()

# Agrupa os registros por 'id_portal'
registros_agrupados = defaultdict(list)
for registro in dados:
    registros_agrupados[registro['id_portal']].append(registro)

# Função para unificar registros
def unificar_registros(registros):
    if not registros:
        return None, []

    # Ordena os registros pelo 'id' para que o menor id esteja primeiro
    registros.sort(key=lambda x: x['id'])

    # O registro resultante começa com os dados do menor id
    registro_unificado = registros[0]

    # Define o 'funcao' do registro de maior id
    registro_unificado['funcao'] = registros[-1]['funcao']

    # Coleta os IDs dos registros a serem excluídos (todos menos o primeiro)
    ids_para_excluir = [registro['id'] for registro in registros[1:]]

    return registro_unificado, ids_para_excluir

# Lista para armazenar os registros unificados
registros_unificados = []
ids_para_excluir = []

# Unifica os registros agrupados
for id_portal, registros in registros_agrupados.items():
    if len(registros) > 1:
        print(f"Unificando registros para id_portal: {id_portal}")
        registro_unificado, ids_excluir = unificar_registros(registros)
        if registro_unificado:
            registros_unificados.append(registro_unificado)
            ids_para_excluir.extend(ids_excluir)

# Atualiza a tabela no Supabase com os registros unificados
for registro_unificado in registros_unificados:
    supabase.table('idServidores_2').upsert(registro_unificado, on_conflict=['id']).execute()

# Exclui os registros com maior ID
for id_excluir in ids_para_excluir:
    supabase.table('idServidores_2').delete().eq('id', id_excluir).execute()
