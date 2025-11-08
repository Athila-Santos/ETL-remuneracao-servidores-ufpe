import pandas as pd
import logging
from typing import Dict, Any, Optional

# Configura um logger para este módulo
logger = logging.getLogger(__name__)

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
        Remove pontos, espaços e substitui vírgulas por pontos.
        """
        if valor_str is None:
            return None
        
        if not isinstance(valor_str, str):
            logger.warning(f"Valor monetário não é string, retornando None. Valor: {valor_str}")
            return None

        try:
            # Limpa a string de caracteres não numéricos (exceto a vírgula)
            valor_limpo = valor_str.replace('.', '').replace(',', '.').replace(" ", "")
            
            # Remove qualquer caractere não numérico/não-ponto (ex: R$)
            valor_limpo = ''.join(c for c in valor_limpo if c.isdigit() or c == '.')
            
            if not valor_limpo:
                return None
                
            return float(valor_limpo)
        except ValueError as e:
            logger.error(f"Não foi possível converter valor monetário '{valor_str}' para float: {e}")
            return None
        except Exception as e:
            logger.error(f"Erro inesperado ao formatar valor '{valor_str}': {e}")
            return None

    def _formatar_data(self, data_str: Optional[str]) -> Optional[str]:
        """
        Formata uma data (string) para o formato 'YYYY-MM-DD'.
        """
        if data_str is None:
            return None
        
        if not isinstance(data_str, str):
            logger.warning(f"Valor de data não é string, retornando None. Valor: {data_str}")
            return None

        try:
            # pd.to_datetime é robusto para lidar com formatos 'dd/mm/YYYY'
            data_obj = pd.to_datetime(data_str, format='%d/%m/%Y').date()
            # Retorna a data formatada como string ISO (YYYY-MM-DD)
            return data_obj.strftime('%Y-%m-%d')
        except ValueError:
            logger.error(f"A data '{data_str}' não está no formato esperado '%d/%m/%Y'.")
            return None
        except Exception as e:
            logger.error(f"Erro inesperado ao formatar data '{data_str}': {e}")
            return None

    def formatar_dados_servidor(self, dados_servidor: Dict[str, Any]) -> Dict[str, Any]:
        """
        Recebe um dicionário de dados brutos do scraper e aplica
        todas as formatações e limpezas necessárias.

        Args:
            dados_servidor: Dicionário com dados extraídos.

        Returns:
            O mesmo dicionário, mas com os valores formatados.
        """
        if not dados_servidor:
            logger.warning("Recebido dicionário de dados vazio para formatação.")
            return {}

        # Faz uma cópia para evitar modificar o original inesperadamente
        dados_formatados = dados_servidor.copy()

        # Aplica as formatações
        dados_formatados['ingresso'] = self._formatar_data(
            dados_servidor.get('ingresso')
        )
        
        dados_formatados['remuneracao_basica_bruta'] = self._formatar_valor_monetario(
            dados_servidor.get('remuneracao_basica_bruta')
        )
        
        dados_formatados['remuneracao_apos_deducoes'] = self._formatar_valor_monetario(
            dados_servidor.get('remuneracao_apos_deducoes')
        )

        # Você pode adicionar outras limpezas aqui se necessário
        # Ex: dados_formatados['jornada'] = self._limpar_campo_jornada(dados_servidor.get('jornada'))

        logger.debug(f"Dados formatados para ID {dados_servidor.get('id_portal')}: {dados_formatados}")
        
        return dados_formatados