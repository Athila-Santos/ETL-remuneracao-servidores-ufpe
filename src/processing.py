import pandas as pd
import logging
import locale
from datetime import datetime
from typing import Dict, Any, Optional

# Configura um logger para este módulo
logger = logging.getLogger(__name__)

# Configura o 'locale' para Português (Brasil) para
# que o Python entenda nomes de meses como "Outubro".
# Se isso falhar, pode ser necessário instalar o pacote de idioma no seu SO.
try:
    locale.setlocale(locale.LC_TIME, 'pt_BR.UTF-8')
except locale.Error:
    try:
        locale.setlocale(locale.LC_TIME, 'Portuguese_Brazil')
    except locale.Error:
        logger.warning("Locale 'pt_BR' não encontrado. Tentando 'Portuguese'. "
                       "Se falhar, a data de remuneração (Mês/Ano) pode não ser formatada.")

class DataProcessor:
    """
    Especialista em limpar, formatar e transformar os dados brutos
    extraídos pelo Scraper.
    """

    def __init__(self):
        logger.info("DataProcessor inicializado.")

    def _formatar_valor_monetario(self, valor_str: Optional[str]) -> Optional[float]:
        """
        Formata um valor monetário (string) para float.
        """
        if valor_str is None:
            return None
        
        if not isinstance(valor_str, str):
            logger.warning(f"Valor monetário não é string: {valor_str}")
            return None

        try:
            valor_limpo = valor_str.replace('.', '').replace(',', '.').replace(" ", "")
            valor_limpo = ''.join(c for c in valor_limpo if c.isdigit() or c == '.')
            
            if not valor_limpo:
                return None
                
            return float(valor_limpo)
        except ValueError as e:
            logger.error(f"Não foi possível converter valor monetário '{valor_str}': {e}")
            return None
        except Exception as e:
            logger.error(f"Erro inesperado ao formatar valor '{valor_str}': {e}")
            return None

    def _formatar_data_padrao(self, data_str: Optional[str]) -> Optional[str]:
        """
        Formata uma data (string) no formato 'dd/mm/YYYY' para 'YYYY-MM-DD'.
        """
        if data_str is None:
            return None
        
        if not isinstance(data_str, str):
            logger.warning(f"Valor de data não é string: {data_str}")
            return None

        try:
            data_obj = pd.to_datetime(data_str, format='%d/%m/%Y').date()
            return data_obj.strftime('%Y-%m-%d')
        except ValueError:
            logger.error(f"A data '{data_str}' não está no formato esperado '%d/%m/%Y'.")
            return None
        except Exception as e:
            logger.error(f"Erro inesperado ao formatar data '{data_str}': {e}")
            return None
            
    def _formatar_data_remuneracao(self, data_str: Optional[str]) -> Optional[str]:
        """
        Formata uma data (string) no formato 'Mês/YYYY' (ex: "Outubro/2025")
        para 'YYYY-MM-DD' (sempre como dia 1º).
        """
        if data_str is None:
            return None
            
        if not isinstance(data_str, str):
            logger.warning(f"Valor de data de remuneração não é string: {data_str}")
            return None
        
        try:
            # Converte "Outubro/2025" para um objeto datetime
            data_obj = datetime.strptime(data_str, '%B/%Y').date()
            # Retorna como string 'YYYY-MM-01'
            return data_obj.strftime('%Y-%m-01')
        except ValueError:
            logger.error(f"A data '{data_str}' não está no formato '%B/%Y' (Mês/Ano).")
            return None
        except Exception as e:
            logger.error(f"Erro inesperado ao formatar data de remuneração '{data_str}': {e}")
            return None

    def formatar_dados_servidor(self, dados_servidor: Dict[str, Any]) -> Dict[str, Any]:
        """
        Recebe um dicionário de dados brutos do scraper e aplica
        todas as formatações e limpezas necessárias.
        """
        if not dados_servidor:
            logger.warning("Recebido dicionário de dados vazio para formatação.")
            return {}

        dados_formatados = {}

        # --- Passa os campos de texto simples ---
        campos_texto = [
            'id_portal', 'cargo_emprego', 'classe_cargo', 
            'regime_juridico', 'jornada', 'afastamento', 
            'uorg_lotacao', 'forma_ingresso'
        ]
        for campo in campos_texto:
            dados_formatados[campo] = dados_servidor.get(campo)

        # --- Formata as datas padrão (dd/mm/YYYY) ---
        dados_formatados['ingresso_orgao'] = self._formatar_data_padrao(
            dados_servidor.get('ingresso_orgao')
        )
        dados_formatados['ingresso_servico_publico'] = self._formatar_data_padrao(
            dados_servidor.get('ingresso_servico_publico')
        )
        
        # --- Formata a data de remuneração (Mês/YYYY) ---
        dados_formatados['data_remuneracao'] = dados_servidor.get('data_remuneracao')

        # --- Formata os valores monetários ---
        dados_formatados['remuneracao_basica_bruta'] = self._formatar_valor_monetario(
            dados_servidor.get('remuneracao_basica_bruta')
        )
        dados_formatados['remuneracao_apos_deducoes'] = self._formatar_valor_monetario(
            dados_servidor.get('remuneracao_apos_deducoes')
        )
        
        # --- Adiciona Metadados ---
        dados_formatados['data_coleta'] = datetime.now().date().isoformat()

        logger.debug(f"Dados formatados para ID {dados_servidor.get('id_portal')}: {dados_formatados}")
        
        # Remove chaves onde o valor é None (opcional, mas limpo para o Supabase)
        dados_limpos = {k: v for k, v in dados_formatados.items() if v is not None}
        
        return dados_limpos