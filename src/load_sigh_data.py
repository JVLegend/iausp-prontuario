"""
Script para carregar e processar múltiplos arquivos CSV do SIGH.

Este módulo carrega todos os CSVs da pasta data/, unifica em um único DataFrame
e processa os dados de pacientes para uso no scraper do PEP.
"""

import os
import pandas as pd
from io import StringIO
from pathlib import Path
from typing import List, Tuple
from icecream import ic
from datetime import datetime


def setup_icecream():
    """Configura icecream com timestamp"""
    ic.configureOutput(prefix=lambda: f'[{datetime.now().strftime("%H:%M:%S")}] ')


def encontrar_csvs(data_dir: str = None) -> List[Path]:
    """
    Encontra todos os arquivos CSV no diretório de dados.

    Args:
        data_dir: Caminho para o diretório de dados (default: ../data)

    Returns:
        Lista de Path objects apontando para os CSVs encontrados
    """
    if data_dir is None:
        # Caminho relativo ao script
        script_dir = Path(__file__).parent
        data_dir = script_dir.parent / "data"
    else:
        data_dir = Path(data_dir)

    ic(f"Procurando CSVs em: {data_dir}")

    if not data_dir.exists():
        ic(f"⚠️ Diretório não existe: {data_dir}")
        return []

    csv_files = list(data_dir.glob("*.csv"))
    ic(f"✓ {len(csv_files)} arquivo(s) CSV encontrado(s)")

    for csv_file in csv_files:
        ic(f"  - {csv_file.name}")

    return csv_files


def carregar_csv_sigh(filepath: Path) -> pd.DataFrame:
    """
    Carrega um arquivo CSV do SIGH com tratamento especial para vírgulas.

    O SIGH exporta CSVs mal-formatados com vírgulas dentro dos campos.
    Esta função trata isso substituindo vírgulas por ' ; ' antes do parse.

    Args:
        filepath: Caminho para o arquivo CSV

    Returns:
        DataFrame com os dados do CSV
    """
    ic(f"Carregando: {filepath.name}")

    try:
        # Ler arquivo e substituir vírgulas
        with open(filepath, "r", encoding="iso-8859-1") as f:
            content = f.read().replace(",", " ; ")

        # Parsear como CSV
        df = pd.read_csv(StringIO(content), sep=" ; ", engine='python')

        # Limpar aspas de todos os valores
        df = df.replace('"', '', regex=True)

        # Limpar aspas dos nomes das colunas
        df.columns = [col.replace('"', '') for col in df.columns]

        ic(f"✓ {len(df)} linhas carregadas de {filepath.name}")
        return df

    except Exception as e:
        ic(f"⚠️ Erro ao carregar {filepath.name}: {e}")
        return pd.DataFrame()


def unificar_dataframes(dataframes: List[pd.DataFrame]) -> pd.DataFrame:
    """
    Unifica múltiplos DataFrames em um único, removendo duplicatas.

    Args:
        dataframes: Lista de DataFrames para unificar

    Returns:
        DataFrame unificado
    """
    ic(f"Unificando {len(dataframes)} DataFrame(s)...")

    if not dataframes:
        ic("⚠️ Nenhum DataFrame para unificar")
        return pd.DataFrame()

    # Concatenar todos os DataFrames
    df_unificado = pd.concat(dataframes, ignore_index=True)
    ic(f"Total de linhas antes de remover duplicatas: {len(df_unificado)}")

    # Remover duplicatas baseado em MATRÍCULA e DATA
    if 'MATRÍCULA' in df_unificado.columns and 'DATA' in df_unificado.columns:
        df_unificado = df_unificado.drop_duplicates(subset=['MATRÍCULA', 'DATA'], keep='first')
        ic(f"✓ Total de linhas após remover duplicatas: {len(df_unificado)}")
    else:
        ic("⚠️ Colunas MATRÍCULA ou DATA não encontradas, mantendo todas as linhas")

    return df_unificado


def processar_dados_pacientes(df: pd.DataFrame) -> Tuple[List[str], List[str], List]:
    """
    Processa o DataFrame e extrai listas de nomes, matrículas e datas.

    Args:
        df: DataFrame com dados dos pacientes

    Returns:
        Tupla com (lista_nomes, lista_matriculas, lista_datas)
    """
    ic("Processando dados dos pacientes...")

    # Extrair listas
    nome_paciente_list = df["NOME PACIENTE"].tolist()
    matricula_list = df["MATRÍCULA"].tolist()

    # Converter DATA para datetime
    df["DATA"] = pd.to_datetime(df["DATA"], format="%d/%m/%Y", errors='coerce')
    data_list = df["DATA"].tolist()

    # Limpar espaços
    nome_paciente_list = [str(name).strip() for name in nome_paciente_list]
    matricula_list = [str(matricula).strip() for matricula in matricula_list]

    # Uppercase nos nomes
    nome_paciente_list = [name.upper() for name in nome_paciente_list]

    # Apenas números na matrícula
    matricula_list = [''.join(filter(str.isdigit, matricula)) for matricula in matricula_list]

    # Remover entradas vazias
    dados_validos = [
        (nome, matricula, data)
        for nome, matricula, data in zip(nome_paciente_list, matricula_list, data_list)
        if matricula  # Só manter se matrícula não estiver vazia
    ]

    if len(dados_validos) < len(nome_paciente_list):
        ic(f"⚠️ {len(nome_paciente_list) - len(dados_validos)} entrada(s) removida(s) por matrícula vazia")

    nome_paciente_list, matricula_list, data_list = zip(*dados_validos) if dados_validos else ([], [], [])
    nome_paciente_list = list(nome_paciente_list)
    matricula_list = list(matricula_list)
    data_list = list(data_list)

    ic(f"✓ {len(matricula_list)} paciente(s) processado(s)")
    ic(f"Exemplo - Nome: {nome_paciente_list[0] if nome_paciente_list else 'N/A'}")
    ic(f"Exemplo - Matrícula: {matricula_list[0] if matricula_list else 'N/A'}")

    return nome_paciente_list, matricula_list, data_list


def carregar_dados_sigh(data_dir: str = None) -> Tuple[pd.DataFrame, List[str], List[str], List]:
    """
    Função principal que carrega todos os CSVs e retorna dados processados.

    Args:
        data_dir: Caminho para o diretório de dados (opcional)

    Returns:
        Tupla com (dataframe_completo, lista_nomes, lista_matriculas, lista_datas)
    """
    setup_icecream()

    ic("="*70)
    ic("CARREGAMENTO DE DADOS DO SIGH")
    ic("="*70)

    # Encontrar CSVs
    csv_files = encontrar_csvs(data_dir)

    if not csv_files:
        ic("❌ Nenhum arquivo CSV encontrado!")
        return pd.DataFrame(), [], [], []

    # Carregar cada CSV
    dataframes = []
    for csv_file in csv_files:
        df = carregar_csv_sigh(csv_file)
        if not df.empty:
            dataframes.append(df)

    if not dataframes:
        ic("❌ Nenhum DataFrame válido carregado!")
        return pd.DataFrame(), [], [], []

    # Unificar DataFrames
    df_unificado = unificar_dataframes(dataframes)

    # Processar dados
    nome_list, matricula_list, data_list = processar_dados_pacientes(df_unificado)

    ic("="*70)
    ic(f"✓✓✓ CARREGAMENTO CONCLUÍDO: {len(matricula_list)} pacientes prontos")
    ic("="*70)

    return df_unificado, nome_list, matricula_list, data_list


def salvar_dataframe_processado(df: pd.DataFrame, output_path: str = None):
    """
    Salva o DataFrame processado em formato Parquet.

    Args:
        df: DataFrame para salvar
        output_path: Caminho de saída (default: data/pacientes_processados.parquet)
    """
    if output_path is None:
        script_dir = Path(__file__).parent
        output_path = script_dir.parent / "data" / "pacientes_processados.parquet"
    else:
        output_path = Path(output_path)

    output_path.parent.mkdir(parents=True, exist_ok=True)

    ic(f"Salvando DataFrame em: {output_path}")
    df.to_parquet(output_path, index=False, compression='snappy')
    ic(f"✓ DataFrame salvo com sucesso ({len(df)} linhas)")


if __name__ == "__main__":
    # Teste do módulo
    df, nomes, matriculas, datas = carregar_dados_sigh()

    if not df.empty:
        print("\n" + "="*70)
        print("RESUMO DOS DADOS CARREGADOS")
        print("="*70)
        print(f"Total de pacientes: {len(matriculas)}")
        print(f"Colunas disponíveis: {list(df.columns)}")
        print(f"\nPrimeiras 3 matrículas: {matriculas[:3]}")
        print(f"Primeiros 3 nomes: {nomes[:3]}")

        # Salvar DataFrame processado
        salvar_dataframe_processado(df)
