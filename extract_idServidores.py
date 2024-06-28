from supabase import create_client, Client
from dotenv import load_dotenv
import os
import requests

# Carregar variáveis de ambiente do arquivo .env
load_dotenv()

# Obter URL e chave do Supabase das variáveis de ambiente
url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")

supabase: Client = create_client(url, key)

def consultar_dados():
    api_url = 'https://portaldatransparencia.gov.br/servidores/consulta/resultado?paginacaoSimples=true&tamanhoPagina=80000&offset=0&direcaoOrdenacao=asc&colunaOrdenacao=nome&orgaosServidorLotacao=OR26242&colunasSelecionadas=detalhar%2Ctipo%2Ccpf%2Cnome%2CorgaoServidorLotacao%2Cmatricula%2Csituacao%2Cfuncao%2Ccargo%2Cquantidade&t=1AEX07LmbjkXuFbhignd&_=1719571776208'

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.93 Safari/537.36'
    }

    response = requests.get(api_url, headers=headers)

    if response.status_code == 200:
        data = response.json()
        registros = []
        for item in data['data']:
            id_portal = item['idComFlagExisteDetalhamentoServidor'].split("_")[0]
            situacao = item['situacao']
            cargo = item['cargo']
            funcao = item['funcao']
            registros.append({
                'id_portal': id_portal,
                'situacao': situacao,
                'cargo': cargo,
                'funcao': funcao
            })
        return registros
    else:
        print(f"Erro na requisição: {response.status_code}")
        return []

dados = consultar_dados()

for registro in dados:
    response = supabase.table('idServidores').insert(registro).execute()
    print(response)