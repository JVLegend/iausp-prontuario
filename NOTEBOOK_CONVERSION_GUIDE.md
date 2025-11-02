# JUPYTER NOTEBOOK CONVERSION GUIDE

**Purpose:** Step-by-step guide to convert the Python scripts into a comprehensive Jupyter notebook

**Date:** 2025-11-02

---

## QUICK START

**Files to analyze:**
- c:/Users/jvict/OneDrive/Documents/GitHub/SuperJV/iausp-prontuario/src/load_sigh_data.py
- c:/Users/jvict/OneDrive/Documents/GitHub/SuperJV/iausp-prontuario/src/pep_scraper.py
- c:/Users/jvict/OneDrive/Documents/GitHub/SuperJV/iausp-prontuario/src/main.py

**Complete analysis available in:**
- COMPREHENSIVE_CODE_ANALYSIS.md (full technical analysis)
- EXECUTIVE_SUMMARY.md (key findings and patterns)

---

## CELL-BY-CELL STRUCTURE

### Cell 1: Imports and Configuration

**Purpose:** Load all dependencies and configure logging

**Source:** All three files (imports section)

```python
# Standard library
import os
import sys
import re
import time
import json
import random
from io import StringIO
from pathlib import Path
from typing import List, Tuple, Dict, Optional
from datetime import datetime

# Data processing
import pandas as pd

# Web automation
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import TimeoutException, NoSuchElementException

# Logging and environment
from icecream import ic
from dotenv import load_dotenv

# Configure icecream with timestamps
ic.configureOutput(prefix=lambda: f'[{datetime.now().strftime("%H:%M:%S")}] ')

print("✓ All imports loaded successfully")
```

---

### Cell 2: Helper Functions

**Purpose:** Utility functions used across the notebook

**Source:** pep_scraper.py (lines 41-43), main.py (lines 44-64)

```python
def get_root_path() -> Path:
    """Retorna o caminho raiz do projeto"""
    # For notebook, get parent of notebook location
    return Path.cwd()

def carregar_credenciais() -> Dict[str, str]:
    """
    Carrega credenciais do arquivo .env ou usa valores padrão.

    Returns:
        Dicionário com usuario, senha, empresa
    """
    load_dotenv()

    credenciais = {
        "usuario": os.getenv("PEP_USUARIO", "matheus.galvao"),
        "senha": os.getenv("PEP_SENHA", "Gimb1994!!!"),
        "empresa": os.getenv("PEP_EMPRESA", "ICHC"),
        "url_destino": os.getenv("PEP_URL", "http://bal-pep.phcnet.usp.br/mvpep/5/pt-BR/#/d/141")
    }

    # Avisar se usando credenciais padrão
    if not os.getenv("PEP_SENHA"):
        ic("⚠️ AVISO: Usando credenciais hardcoded! Configure arquivo .env")

    return credenciais

print("✓ Helper functions loaded")
```

---

### Cell 3: Data Loading Functions (CSV Processing)

**Purpose:** Load and process patient data from SIGH CSVs

**Source:** load_sigh_data.py (entire file)

**CRITICAL:** Copy these functions EXACTLY as-is:

```python
def encontrar_csvs(data_dir: str = None) -> List[Path]:
    """
    Encontra todos os arquivos CSV no diretório de dados.

    Args:
        data_dir: Caminho para o diretório de dados (default: ./data)

    Returns:
        Lista de Path objects apontando para os CSVs encontrados
    """
    if data_dir is None:
        root = get_root_path()
        data_dir = root / "data"
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

print("✓ Data loading functions loaded")
```

---

### Cell 4: Selenium Setup Functions

**Purpose:** Configure WebDriver and perform login

**Source:** pep_scraper.py (lines 50-191)

```python
def configurar_driver() -> webdriver.Chrome:
    """
    Configura e retorna o driver do Selenium.

    Returns:
        WebDriver configurado e pronto para uso
    """
    root = get_root_path()

    # Caminhos
    cent_path = r"C:\CentBrowser\chrome.exe"
    driver_path = root / "3rdparty" / "chromedriver.exe"

    ic(f"Driver path: {driver_path}")

    # Configurar opções
    options = Options()
    options.binary_location = cent_path

    # Opções anti-detecção
    options.add_argument("--cb-disable-components-auto-update")
    options.add_argument("--start-maximized")
    options.add_argument("--ignore-certificate-errors")
    options.add_argument("--allow-insecure-localhost")
    options.add_argument("--disable-direct-write")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)

    # Configurar service
    service = Service(executable_path=str(driver_path))

    ic("Iniciando navegador...")
    driver = webdriver.Chrome(service=service, options=options)

    return driver


def fazer_login(driver: webdriver.Chrome, usuario: str, senha: str, empresa: str) -> bool:
    """
    Realiza login no sistema MV.

    Args:
        driver: WebDriver do Selenium
        usuario: Nome de usuário
        senha: Senha
        empresa: Nome da empresa

    Returns:
        True se login bem-sucedido, False caso contrário
    """
    try:
        url = "http://hishc.phcnet.usp.br"
        ic("="*70)
        ic("ETAPA 1: LOGIN")
        ic("="*70)
        ic(f"Navegando para: {url}")

        driver.get(url)
        wait = WebDriverWait(driver, 10)

        ic(f"URL atual: {driver.current_url}")
        ic(f"Título: {driver.title}")

        # Aguardar formulário
        ic("Aguardando formulário de login...")
        username_field = wait.until(
            EC.presence_of_element_located((By.ID, "username"))
        )
        ic("✓ Formulário carregado!")

        # Preencher usuário
        ic(f"Preenchendo usuário: {usuario}")
        username_field.clear()
        username_field.send_keys(usuario)

        # Preencher senha
        ic("Preenchendo senha...")
        password_field = driver.find_element(By.ID, "password")
        password_field.clear()
        password_field.send_keys(senha)

        time.sleep(1)

        # Selecionar empresa
        ic(f"Selecionando empresa: {empresa}")
        company_select_element = wait.until(
            EC.presence_of_element_located((By.ID, "companies"))
        )

        company_select = Select(company_select_element)

        # Tentar selecionar empresa
        try:
            company_select.select_by_visible_text(empresa)
            ic(f"✓ Empresa '{empresa}' selecionada por texto!")
        except:
            try:
                company_select.select_by_value(empresa)
                ic(f"✓ Empresa '{empresa}' selecionada por value!")
            except:
                for option in company_select.options:
                    if empresa.upper() in option.text.upper():
                        company_select.select_by_visible_text(option.text)
                        ic(f"✓ Empresa '{option.text}' selecionada!")
                        break

        time.sleep(1)

        # Submeter formulário
        ic("Submetendo formulário...")
        submit_button = driver.find_element(By.CSS_SELECTOR, "input.btn-submit[type='submit']")
        submit_button.click()

        ic("Aguardando login processar...")
        time.sleep(5)

        ic(f"URL atual: {driver.current_url}")
        ic(f"Título: {driver.title}")

        # Verificar sucesso
        if "login" in driver.current_url.lower():
            ic("⚠️ AVISO: Ainda na página de login!")
            root = get_root_path()
            driver.save_screenshot(str(root / "errors" / "erro_login.png"))
            return False
        else:
            ic("✓ Login realizado com sucesso!")
            return True

    except Exception as e:
        ic(f"⚠️ Erro no login: {e}")
        root = get_root_path()
        driver.save_screenshot(str(root / "errors" / "erro_login_exception.png"))
        return False


def navegar_para_pagina(driver: webdriver.Chrome, url: str) -> bool:
    """
    Navega para uma URL específica.

    Args:
        driver: WebDriver do Selenium
        url: URL de destino

    Returns:
        True se navegação bem-sucedida
    """
    try:
        ic("="*70)
        ic("ETAPA 2: NAVEGAÇÃO")
        ic("="*70)
        ic(f"Acessando: {url}")

        driver.get(url)

        ic("Aguardando página Angular carregar...")
        time.sleep(8)  # Angular precisa de mais tempo

        ic(f"URL atual: {driver.current_url}")
        ic(f"Título: {driver.title}")
        ic("✓ Página carregada!")

        return True

    except Exception as e:
        ic(f"⚠️ Erro na navegação: {e}")
        root = get_root_path()
        driver.save_screenshot(str(root / "errors" / "erro_navegacao.png"))
        return False

print("✓ Selenium setup functions loaded")
```

---

### Cell 5: Patient Search and Selection Functions

**Purpose:** Search for patient and navigate to record

**Source:** pep_scraper.py (lines 237-526)

**IMPORTANT:** These functions use multi-strategy selectors - preserve ALL strategies

```python
# [Copy buscar_paciente() function - lines 237-369 from pep_scraper.py]
# [Copy selecionar_paciente() function - lines 376-526 from pep_scraper.py]

# See COMPREHENSIVE_CODE_ANALYSIS.md for full code
# Key features:
# - 10+ selector strategies
# - Heuristic fallbacks
# - Multiple button search strategies
# - Debug screenshots on error

print("✓ Patient search/selection functions loaded")
```

---

### Cell 6: CRITICAL - Multiple Attendances Capture

**Purpose:** THE GAME-CHANGER - Capture ALL historical attendances

**Source:** pep_scraper.py (lines 533-734)

**⚠️ THIS IS THE MOST IMPORTANT CELL - DO NOT SIMPLIFY**

```python
def clicar_em_todos_atendimentos(driver: webdriver.Chrome) -> List:
    """
    Clica em cada item do histórico de atendimentos (lado direito) e retorna lista de elementos.

    Args:
        driver: WebDriver do Selenium

    Returns:
        Lista de elementos clicáveis do histórico
    """
    ic("Procurando lista de atendimentos no histórico...")

    # Possíveis seletores para os itens do histórico (lado direito)
    historico_selectors = [
        "div.historico-item",
        "div[class*='historico']",
        "div[class*='lista'] div[class*='item']",
        "mat-list-item",
        "div[role='listitem']",
        ".history-item",
        ".timeline-item",
        # Seletores que contenham data (formato DD/MM/YYYY HH:MM)
        "//div[contains(text(), '/') and contains(text(), ':')]/..",
        # Elementos clicáveis que tenham texto com data
        "//*[contains(@class, 'clickable') or @role='button'][.//*[contains(text(), '/')]]",
    ]

    itens_historico = []

    for selector in historico_selectors:
        try:
            if selector.startswith('//'):
                elements = driver.find_elements(By.XPATH, selector)
            else:
                elements = driver.find_elements(By.CSS_SELECTOR, selector)

            if elements:
                # Filtrar apenas elementos visíveis e clicáveis
                elementos_visiveis = [
                    elem for elem in elements
                    if elem.is_displayed() and elem.is_enabled()
                ]

                if elementos_visiveis:
                    ic(f"✓ Encontrados {len(elementos_visiveis)} itens com seletor: {selector}")
                    itens_historico = elementos_visiveis
                    break
        except:
            continue

    if not itens_historico:
        ic("⚠️ Tentando estratégia alternativa: procurar por textos com data...")

        # Estratégia alternativa: procurar qualquer elemento que contenha data/hora
        try:
            # Procurar elementos que contenham padrão DD/MM/YYYY HH:MM
            all_elements = driver.find_elements(
                By.XPATH,
                "//*[contains(text(), '/') and contains(text(), ':') and string-length(text()) >= 16]"
            )

            # Pegar os elementos pais (que são clicáveis)
            parent_elements = []
            for elem in all_elements:
                try:
                    parent = elem.find_element(By.XPATH, "..")
                    if parent.is_displayed() and parent not in parent_elements:
                        parent_elements.append(parent)
                except:
                    continue

            if parent_elements:
                ic(f"✓ Encontrados {len(parent_elements)} itens via estratégia alternativa")
                itens_historico = parent_elements
        except Exception as e:
            ic(f"⚠️ Erro na estratégia alternativa: {e}")

    return itens_historico


def capturar_dados_atendimento(driver: webdriver.Chrome, index: int = None) -> Optional[Dict]:
    """
    Captura dados de UM ÚNICO atendimento (o que está atualmente selecionado).

    Args:
        driver: WebDriver do Selenium
        index: Índice do atendimento (para referência no log)

    Returns:
        Dicionário com os dados do atendimento ou None
    """
    prefix = f"[Atendimento {index}] " if index is not None else ""

    try:
        ic(f"{prefix}Capturando dados do atendimento...")

        # Aguardar página carregar
        time.sleep(2)

        # Dicionário para armazenar os dados deste atendimento
        dados_atendimento = {
            "data_atendimento": "",
            "especialidade": "",
            "medico": "",
            "diagnostico": "",
            "subespecialidade": "",
            "historico_anamnese": "",
            "texto_completo": "",
            "data_captura": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

        # Capturar todo o texto visível da área de conteúdo
        try:
            # Tentar encontrar área de conteúdo principal
            content_selectors = [
                "div[class*='content']",
                "div[class*='conteudo']",
                "mat-card-content",
                "div[role='main']",
                ".seguimento",
                ".atendimento-content"
            ]

            conteudo_element = None
            for selector in content_selectors:
                try:
                    conteudo_element = driver.find_element(By.CSS_SELECTOR, selector)
                    if conteudo_element.is_displayed():
                        break
                except:
                    continue

            if conteudo_element:
                dados_atendimento["texto_completo"] = conteudo_element.text
            else:
                # Fallback: pegar body inteiro
                dados_atendimento["texto_completo"] = driver.find_element(By.TAG_NAME, "body").text

            page_text = dados_atendimento["texto_completo"]

        except Exception as e:
            ic(f"{prefix}⚠️ Erro ao capturar texto: {e}")
            page_text = ""

        # Estratégias de captura via regex
        patterns = {
            "data_atendimento": [
                r'(\d{2}/\d{2}/\d{4}\s+\d{2}:\d{2})',  # DD/MM/YYYY HH:MM
                r'Data[:\s]*(\d{2}/\d{2}/\d{4})',
            ],
            "subespecialidade": [
                r'Subespecialidade\s*\(por[:\s]*([^\n]+)',
                r'Subespecialidade[:\s]*([^\n]+)',
            ],
            "diagnostico": [
                r'Diagnóstico\s*\(por[:\s]*([^\n]+)',
                r'Diagnóstico[:\s]*([^\n]+)',
                r'Descolamento de retina[^\n]*',
            ],
            "medico": [
                r'(?:Dr\.|Dra\.)\s*([A-Z\s]+)',
            ]
        }

        for campo, padroes in patterns.items():
            if not dados_atendimento[campo]:
                for padrao in padroes:
                    match = re.search(padrao, page_text, re.IGNORECASE)
                    if match:
                        valor = match.group(1).strip() if match.lastindex >= 1 else match.group(0).strip()
                        dados_atendimento[campo] = valor
                        ic(f"{prefix}✓ {campo}: {valor}")
                        break

        # Capturar histórico/anamnese (geralmente texto longo)
        try:
            # Procurar por seções de texto longo
            historico_patterns = [
                r'Históri[oc]o/Anamnese[:\s]*(.{50,}?)(?=\n\n|\Z)',
                r'POS RETIR[^\n]+\n(.{50,}?)(?=\n\n|\Z)',
            ]

            for pattern in historico_patterns:
                match = re.search(pattern, page_text, re.IGNORECASE | re.DOTALL)
                if match:
                    dados_atendimento["historico_anamnese"] = match.group(1).strip()[:500]  # Limitar a 500 chars
                    ic(f"{prefix}✓ Histórico capturado ({len(dados_atendimento['historico_anamnese'])} chars)")
                    break
        except:
            pass

        # Verificar se capturou algo útil
        campos_preenchidos = sum(1 for k, v in dados_atendimento.items()
                                if k not in ["texto_completo", "data_captura"] and v)

        ic(f"{prefix}Campos capturados: {campos_preenchidos}/5")

        return dados_atendimento

    except Exception as e:
        ic(f"{prefix}⚠️ Erro ao capturar atendimento: {e}")
        return None

print("✓ CRITICAL: Multiple attendances capture functions loaded")
```

---

### Cell 7: Main Data Capture Function

**Purpose:** Capture patient demographics + loop through all attendances

**Source:** pep_scraper.py (lines 737-1087)

**⚠️ THIS CELL CONTAINS THE MAIN LOOP - CRITICAL**

```python
def capturar_dados_paciente(driver: webdriver.Chrome, prontuario: str) -> Optional[Dict]:
    """
    Captura os dados do paciente da página do PEP.
    NOVA VERSÃO: Clica em todos os atendimentos do histórico e captura dados de cada um.

    Args:
        driver: WebDriver do Selenium
        prontuario: Número do prontuário

    Returns:
        Dicionário com os dados capturados incluindo lista de todos os atendimentos
    """
    try:
        ic("="*70)
        ic("ETAPA 5: CAPTURA DE DADOS DO PACIENTE + HISTÓRICO")
        ic("="*70)

        wait = WebDriverWait(driver, 10)

        ic("Aguardando página carregar completamente...")
        time.sleep(4)

        # ==================================================================
        # NOVO: CAPTURAR MÚLTIPLOS ATENDIMENTOS
        # ==================================================================

        # Primeiro, encontrar todos os itens do histórico
        itens_historico = clicar_em_todos_atendimentos(driver)

        if not itens_historico:
            ic("⚠️ Nenhum item de histórico encontrado, continuando com dados demográficos apenas...")
            lista_atendimentos = []
        else:
            ic(f"✓ Encontrados {len(itens_historico)} atendimento(s) no histórico")

            lista_atendimentos = []

            # Clicar em cada item e capturar os dados
            for i, item in enumerate(itens_historico, 1):
                try:
                    ic(f"\n{'='*70}")
                    ic(f"Processando atendimento {i}/{len(itens_historico)}")
                    ic(f"{'='*70}")

                    # Scroll até o elemento para garantir que está visível
                    try:
                        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", item)
                        time.sleep(0.5)
                    except:
                        pass

                    # Clicar no item
                    try:
                        item.click()
                        ic(f"✓ Clicado no atendimento {i}")
                    except:
                        # Tentar via JavaScript se click normal falhar
                        try:
                            driver.execute_script("arguments[0].click();", item)
                            ic(f"✓ Clicado no atendimento {i} (via JavaScript)")
                        except Exception as e:
                            ic(f"⚠️ Erro ao clicar no atendimento {i}: {e}")
                            continue

                    # Aguardar conteúdo carregar
                    time.sleep(2)

                    # Aguardar loading desaparecer (se houver)
                    try:
                        WebDriverWait(driver, 5).until(
                            EC.invisibility_of_element_located((By.CLASS_NAME, "pep-loading-wrapper"))
                        )
                    except:
                        pass

                    # Capturar dados deste atendimento
                    dados_atendimento = capturar_dados_atendimento(driver, index=i)

                    if dados_atendimento:
                        lista_atendimentos.append(dados_atendimento)
                        ic(f"✓ Atendimento {i} capturado com sucesso")
                    else:
                        ic(f"⚠️ Falha ao capturar dados do atendimento {i}")

                except Exception as e:
                    ic(f"⚠️ Erro ao processar atendimento {i}: {e}")
                    continue

            ic(f"\n{'='*70}")
            ic(f"✓ Total de atendimentos capturados: {len(lista_atendimentos)}/{len(itens_historico)}")
            ic(f"{'='*70}\n")

        # ==================================================================
        # DADOS DEMOGRÁFICOS DO PACIENTE (MANTIDO DO CÓDIGO ORIGINAL)
        # ==================================================================

        # Estrutura de dados (dados demográficos + lista de atendimentos)
        dados_paciente = {
            "prontuario": prontuario,
            "nome_registro": "",
            "data_nascimento": "",
            "raca": "",
            "cpf": "",
            "codigo_paciente": "",
            "naturalidade": "",
            "atendimentos": lista_atendimentos,  # NOVO: lista de todos os atendimentos capturados
            "total_atendimentos": len(lista_atendimentos),  # NOVO: contador
            "data_captura": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

        ic("Iniciando captura de dados do sistema PEP...")

        # [Continue with demographic capture strategies - 4 strategies]
        # [See lines 849-1024 in pep_scraper.py]
        # [Copy the entire demographic capture section]

        # Resumo
        ic("="*70)
        ic("RESUMO DA CAPTURA:")
        ic("="*70)

        dados_capturados = 0
        dados_faltantes = []

        # Campos demográficos para validação (excluindo campos especiais)
        campos_demograficos = ["nome_registro", "data_nascimento", "raca", "cpf", "codigo_paciente", "naturalidade"]

        for campo in campos_demograficos:
            valor = dados_paciente.get(campo, "")
            if valor:
                ic(f"✓ {campo.replace('_', ' ').title()}: {valor}")
                dados_capturados += 1
            else:
                ic(f"✗ {campo.replace('_', ' ').title()}: (não capturado)")
                dados_faltantes.append(campo)

        ic(f"Total demográficos: {dados_capturados}/6 dados capturados")
        ic(f"Total atendimentos: {len(lista_atendimentos)} capturado(s)")

        # Salvar JSON
        root = get_root_path()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"paciente_{prontuario}_{timestamp}.json"

        dados_dir = root / "dados_pacientes"
        dados_dir.mkdir(parents=True, exist_ok=True)

        filepath = dados_dir / filename

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(dados_paciente, f, ensure_ascii=False, indent=4)

        ic(f"✓ Dados salvos em: {filepath}")

        # Salvar debug se houver falhas
        if dados_faltantes:
            ic(f"⚠️ Dados não capturados: {', '.join(dados_faltantes)}")

            html_filename = f"page_source_{prontuario}_{timestamp}.html"
            html_filepath = dados_dir / html_filename

            with open(html_filepath, "w", encoding="utf-8") as f:
                f.write(driver.page_source)

            ic(f"✓ HTML salvo para debug em: {html_filepath}")

            screenshot_filename = f"screenshot_{prontuario}_{timestamp}.png"
            screenshot_filepath = dados_dir / screenshot_filename
            driver.save_screenshot(str(screenshot_filepath))
            ic(f"✓ Screenshot salvo em: {screenshot_filepath}")

        return dados_paciente

    except Exception as e:
        ic(f"⚠️ Erro ao capturar dados: {e}")
        root = get_root_path()
        driver.save_screenshot(str(root / "errors" / "erro_captura_dados.png"))
        return None

print("✓ Main data capture function loaded")
```

---

### Cell 8: Checkpoint System Functions

**Purpose:** Track progress and enable resumable processing

**Source:** main.py (lines 71-153)

```python
def carregar_checkpoint() -> Dict:
    """
    Carrega checkpoint do processamento anterior.

    Returns:
        Dicionário com dados do checkpoint
    """
    root = get_root_path()
    checkpoint_file = root / "checkpoint.json"

    if checkpoint_file.exists():
        try:
            with open(checkpoint_file, "r", encoding="utf-8") as f:
                checkpoint = json.load(f)
            ic(f"✓ Checkpoint carregado: {len(checkpoint.get('processados', []))} pacientes já processados")
            return checkpoint
        except Exception as e:
            ic(f"⚠️ Erro ao carregar checkpoint: {e}")
            return {"processados": [], "falhas": [], "inicio": datetime.now().isoformat()}
    else:
        ic("Nenhum checkpoint encontrado, iniciando do zero")
        return {"processados": [], "falhas": [], "inicio": datetime.now().isoformat()}


def salvar_checkpoint(checkpoint: Dict):
    """
    Salva checkpoint do processamento.

    Args:
        checkpoint: Dicionário com dados do checkpoint
    """
    root = get_root_path()
    checkpoint_file = root / "checkpoint.json"

    try:
        checkpoint["ultima_atualizacao"] = datetime.now().isoformat()
        with open(checkpoint_file, "w", encoding="utf-8") as f:
            json.dump(checkpoint, f, ensure_ascii=False, indent=4)
    except Exception as e:
        ic(f"⚠️ Erro ao salvar checkpoint: {e}")


def adicionar_ao_checkpoint(checkpoint: Dict, matricula: str, sucesso: bool, motivo: str = ""):
    """
    Adiciona um paciente ao checkpoint.

    Args:
        checkpoint: Dicionário do checkpoint
        matricula: Número da matrícula
        sucesso: Se processamento foi bem-sucedido
        motivo: Motivo da falha (se aplicável)
    """
    if sucesso:
        checkpoint["processados"].append({
            "matricula": matricula,
            "timestamp": datetime.now().isoformat(),
            "sucesso": True
        })
    else:
        checkpoint["falhas"].append({
            "matricula": matricula,
            "timestamp": datetime.now().isoformat(),
            "sucesso": False,
            "motivo": motivo
        })

    salvar_checkpoint(checkpoint)


def ja_foi_processado(checkpoint: Dict, matricula: str) -> bool:
    """
    Verifica se uma matrícula já foi processada com sucesso.

    Args:
        checkpoint: Dicionário do checkpoint
        matricula: Número da matrícula

    Returns:
        True se já foi processado
    """
    matriculas_processadas = [p["matricula"] for p in checkpoint.get("processados", [])]
    return matricula in matriculas_processadas

print("✓ Checkpoint functions loaded")
```

---

### Cell 9: Processing Functions

**Purpose:** Single patient and batch processing logic

**Source:** main.py (lines 160-317)

```python
def processar_paciente(driver, matricula: str, nome: str, credenciais: Dict) -> bool:
    """
    Processa um único paciente: busca, seleciona e captura dados.

    Args:
        driver: WebDriver do Selenium
        matricula: Número da matrícula (prontuário)
        nome: Nome do paciente (para referência)
        credenciais: Dicionário com credenciais

    Returns:
        True se processamento bem-sucedido
    """
    try:
        ic(f"Processando: {nome} (Matrícula: {matricula})")

        # Buscar paciente
        if not buscar_paciente(driver, matricula):
            ic(f"❌ Falha na busca do paciente {matricula}")
            return False

        # Selecionar paciente
        if not selecionar_paciente(driver, matricula):
            ic(f"❌ Falha na seleção do paciente {matricula}")
            return False

        # Capturar dados
        dados = capturar_dados_paciente(driver, matricula)
        if not dados:
            ic(f"⚠️ Falha na captura de dados do paciente {matricula}")
            return False

        ic(f"✓ Paciente {matricula} processado com sucesso!")

        # Voltar para página de busca para próximo paciente
        navegar_para_pagina(driver, credenciais["url_destino"])

        return True

    except Exception as e:
        ic(f"⚠️ Erro ao processar paciente {matricula}: {e}")
        return False


def processar_lista_pacientes(
    matriculas: List[str],
    nomes: List[str],
    credenciais: Dict,
    limite: Optional[int] = None,
    intervalo_min: int = 5,
    intervalo_max: int = 15
):
    """
    Processa lista de pacientes em loop.

    Args:
        matriculas: Lista de matrículas
        nomes: Lista de nomes dos pacientes
        credenciais: Dicionário com credenciais
        limite: Limite de pacientes a processar (None = todos)
        intervalo_min: Intervalo mínimo entre pacientes (segundos)
        intervalo_max: Intervalo máximo entre pacientes (segundos)
    """
    ic("="*70)
    ic("INÍCIO DO PROCESSAMENTO EM LOTE")
    ic("="*70)

    # Carregar checkpoint
    checkpoint = carregar_checkpoint()

    # Filtrar pacientes já processados
    pacientes_pendentes = [
        (mat, nom) for mat, nom in zip(matriculas, nomes)
        if not ja_foi_processado(checkpoint, mat)
    ]

    ic(f"Total de pacientes: {len(matriculas)}")
    ic(f"Já processados: {len(matriculas) - len(pacientes_pendentes)}")
    ic(f"Pendentes: {len(pacientes_pendentes)}")

    if limite:
        pacientes_pendentes = pacientes_pendentes[:limite]
        ic(f"⚠️ MODO TESTE: Processando apenas {limite} pacientes")

    if not pacientes_pendentes:
        ic("✓ Todos os pacientes já foram processados!")
        return

    # Configurar driver
    ic("Configurando WebDriver...")
    driver = None

    try:
        driver = configurar_driver()

        # Fazer login
        ic("Fazendo login...")
        if not fazer_login(driver, credenciais["usuario"], credenciais["senha"], credenciais["empresa"]):
            ic("❌ Falha no login. Encerrando...")
            return

        # Navegar para página de busca
        ic("Navegando para página de busca...")
        if not navegar_para_pagina(driver, credenciais["url_destino"]):
            ic("❌ Falha na navegação. Encerrando...")
            return

        # Processar cada paciente
        sucessos = 0
        falhas = 0

        for i, (matricula, nome) in enumerate(pacientes_pendentes, 1):
            ic("="*70)
            ic(f"[{i}/{len(pacientes_pendentes)}] Processando paciente...")
            ic("="*70)

            sucesso = processar_paciente(driver, matricula, nome, credenciais)

            if sucesso:
                adicionar_ao_checkpoint(checkpoint, matricula, True)
                sucessos += 1
            else:
                adicionar_ao_checkpoint(checkpoint, matricula, False, "Erro no processamento")
                falhas += 1

            # Rate limiting: delay aleatório entre pacientes
            if i < len(pacientes_pendentes):  # Não esperar após o último
                intervalo = random.randint(intervalo_min, intervalo_max)
                ic(f"⏳ Aguardando {intervalo}s antes do próximo paciente...")
                time.sleep(intervalo)

        # Resumo final
        ic("="*70)
        ic("PROCESSAMENTO CONCLUÍDO")
        ic("="*70)
        ic(f"✓ Sucessos: {sucessos}")
        ic(f"✗ Falhas: {falhas}")
        ic(f"Taxa de sucesso: {(sucessos / (sucessos + falhas) * 100):.1f}%")

    except KeyboardInterrupt:
        ic("\n⚠️ Processamento interrompido pelo usuário")
        ic(f"Checkpoint salvo. Execute novamente para continuar de onde parou.")

    except Exception as e:
        ic(f"❌ Erro geral: {e}")
        import traceback
        traceback.print_exc()

    finally:
        if driver:
            ic("Fechando navegador...")
            driver.quit()

print("✓ Processing functions loaded")
```

---

### Cell 10: EXECUTE - Load Data

**Purpose:** Load CSVs and credentials

```python
# Load patient data from CSVs
df, nomes, matriculas, datas = carregar_dados_sigh()

# Load credentials
credenciais = carregar_credenciais()

# Summary
print("\n" + "="*70)
print("DADOS CARREGADOS")
print("="*70)
print(f"Total de pacientes: {len(matriculas)}")
print(f"Primeiros 3 nomes: {nomes[:3]}")
print(f"Primeiras 3 matrículas: {matriculas[:3]}")
print("="*70)
```

---

### Cell 11: EXECUTE - Test Mode (Single Patient)

**Purpose:** Test with 1 patient to verify everything works

```python
# Test with single patient
if len(matriculas) > 0:
    print("\n🧪 MODO TESTE: Processando 1 paciente")
    print("="*70)

    driver = configurar_driver()

    try:
        # Login
        if fazer_login(driver, credenciais["usuario"], credenciais["senha"], credenciais["empresa"]):
            # Navigate
            if navegar_para_pagina(driver, credenciais["url_destino"]):
                # Process single patient
                teste_matricula = matriculas[0]
                teste_nome = nomes[0]

                sucesso = processar_paciente(driver, teste_matricula, teste_nome, credenciais)

                if sucesso:
                    print("\n✅ TESTE BEM-SUCEDIDO!")
                    print(f"Verifique o arquivo JSON em dados_pacientes/paciente_{teste_matricula}_*.json")
                else:
                    print("\n❌ TESTE FALHOU - Verifique logs e screenshots")
    finally:
        driver.quit()
        print("\n✓ Navegador fechado")
else:
    print("❌ Nenhum paciente carregado para teste")
```

---

### Cell 12: EXECUTE - Batch Mode (Multiple Patients)

**Purpose:** Process multiple patients (5 for testing, all for production)

```python
# Ask user for mode
print("\n" + "="*70)
print("MODO DE PROCESSAMENTO")
print("="*70)
resposta = input("Processar apenas os primeiros 5 pacientes? (s/N): ").strip().lower()

if resposta == 's':
    limite = 5
    print("⚠️ MODO TESTE: 5 pacientes")
else:
    resposta_confirma = input(
        f"\n⚠️ Você está prestes a processar {len(matriculas)} pacientes.\n"
        f"Isso levará aproximadamente {len(matriculas) * 45 / 3600:.1f} horas.\n"
        f"Continuar? (s/N): "
    ).strip().lower()

    if resposta_confirma != 's':
        print("❌ Processamento cancelado")
        limite = None
    else:
        limite = None
        print("🚀 MODO PRODUÇÃO: Todos os pacientes")

if limite is not None or resposta_confirma == 's':
    # Execute batch processing
    processar_lista_pacientes(
        matriculas=matriculas,
        nomes=nomes,
        credenciais=credenciais,
        limite=limite,
        intervalo_min=5,
        intervalo_max=15
    )

    print("\n" + "="*70)
    print("✅ PROCESSAMENTO CONCLUÍDO")
    print("="*70)
```

---

### Cell 13: ANALYZE - Results

**Purpose:** Analyze captured data

```python
import json
from pathlib import Path

# Find all JSON files
dados_dir = Path.cwd() / "dados_pacientes"
json_files = list(dados_dir.glob("paciente_*.json"))

print("="*70)
print("ANÁLISE DOS RESULTADOS")
print("="*70)
print(f"Total de pacientes processados: {len(json_files)}")

if json_files:
    # Load and analyze
    total_attendances = 0
    min_attendances = float('inf')
    max_attendances = 0

    for file in json_files:
        with open(file, "r", encoding="utf-8") as f:
            data = json.load(f)
            num_atend = data.get("total_atendimentos", 0)
            total_attendances += num_atend
            min_attendances = min(min_attendances, num_atend)
            max_attendances = max(max_attendances, num_atend)

    avg_attendances = total_attendances / len(json_files)

    print(f"\nATENDIMENTOS CAPTURADOS:")
    print(f"  Total: {total_attendances}")
    print(f"  Média por paciente: {avg_attendances:.1f}")
    print(f"  Mínimo: {min_attendances}")
    print(f"  Máximo: {max_attendances}")

    # Show sample
    print(f"\nAMOSTRA - Primeiro paciente:")
    with open(json_files[0], "r", encoding="utf-8") as f:
        sample = json.load(f)
        print(f"  Prontuário: {sample.get('prontuario', 'N/A')}")
        print(f"  Nome: {sample.get('nome_registro', 'N/A')}")
        print(f"  Atendimentos: {sample.get('total_atendimentos', 0)}")
        if sample.get('atendimentos'):
            print(f"\n  Primeiro atendimento:")
            primeiro = sample['atendimentos'][0]
            print(f"    Data: {primeiro.get('data_atendimento', 'N/A')}")
            print(f"    Médico: {primeiro.get('medico', 'N/A')}")
            print(f"    Diagnóstico: {primeiro.get('diagnostico', 'N/A')}")
else:
    print("⚠️ Nenhum arquivo JSON encontrado")

print("="*70)
```

---

## TESTING CHECKLIST

After creating the notebook, test these in order:

### Phase 1: Basic Setup
- [ ] Cell 1: All imports work without errors
- [ ] Cell 2: Helper functions defined
- [ ] Cell 3: Data loading functions defined
- [ ] Cell 4: Selenium functions defined
- [ ] Cell 5: Search/selection functions defined
- [ ] Cell 6: **CRITICAL** - Multiple attendances functions defined
- [ ] Cell 7: Main capture function defined
- [ ] Cell 8: Checkpoint functions defined
- [ ] Cell 9: Processing functions defined

### Phase 2: Data Loading
- [ ] Cell 10: CSVs loaded successfully
- [ ] Cell 10: At least 1 patient found
- [ ] Cell 10: Credentials loaded (check .env or defaults)

### Phase 3: Single Patient Test
- [ ] Cell 11: Browser opens
- [ ] Cell 11: Login succeeds
- [ ] Cell 11: Navigation succeeds
- [ ] Cell 11: Patient search succeeds
- [ ] Cell 11: Patient selection succeeds
- [ ] Cell 11: **CRITICAL** - Multiple attendances found
- [ ] Cell 11: **CRITICAL** - lista_atendimentos has > 1 item
- [ ] Cell 11: JSON file created
- [ ] Cell 11: JSON contains "atendimentos" array
- [ ] Cell 11: "total_atendimentos" > 0

### Phase 4: Batch Processing (5 patients)
- [ ] Cell 12: Checkpoint created/loaded
- [ ] Cell 12: 5 patients processed
- [ ] Cell 12: Rate limiting works (5-15s delays)
- [ ] Cell 12: Success rate > 80%
- [ ] Cell 12: Can interrupt (Ctrl+C) and resume

### Phase 5: Results Validation
- [ ] Cell 13: JSON files found
- [ ] Cell 13: Average attendances > 5
- [ ] Cell 13: Data structure correct

### Phase 6: Production Run
- [ ] Cell 12: Full batch processing (all patients)
- [ ] Monitor: No crashes for 1+ hour
- [ ] Monitor: Checkpoint saves every patient
- [ ] Monitor: Can resume after interruption

---

## COMMON ISSUES AND SOLUTIONS

### Issue 1: "Element not clickable"
**Solution:** Ensure scroll before click (line in Cell 7):
```python
driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", item)
time.sleep(0.5)
```

### Issue 2: "No history items found"
**Solution:** Check if clicar_em_todos_atendimentos() is trying all strategies. May need to add new selectors.

### Issue 3: "Only 1 attendance captured"
**Solution:** Verify loop in Cell 7 is iterating over all itens_historico. Check logs for click failures.

### Issue 4: "Checkpoint not working"
**Solution:** Verify checkpoint.json is being created in project root. Check file permissions.

### Issue 5: "Browser detected as bot"
**Solution:** Increase intervalo_min and intervalo_max in Cell 12 (e.g., 10-30s).

---

## PERFORMANCE OPTIMIZATION TIPS

### For Testing (Speed)
```python
# In Cell 12
intervalo_min=2   # Fast delays
intervalo_max=5
```

### For Production (Safety)
```python
# In Cell 12
intervalo_min=10  # Safer delays
intervalo_max=30
```

### Memory Management
- Close browser every 100 patients:
```python
# In processar_lista_pacientes(), add:
if i % 100 == 0:
    driver.quit()
    driver = configurar_driver()
    fazer_login(driver, ...)
```

---

## FINAL NOTES

**Most Important Cells:**
1. Cell 6 (clicar_em_todos_atendimentos)
2. Cell 7 (capturar_dados_paciente with loop)

**These two cells contain the GAME-CHANGING feature. Do NOT simplify or skip.**

**Success Criteria:**
- ✅ lista_atendimentos has multiple items (avg 10+)
- ✅ JSON files contain "atendimentos" array
- ✅ "total_atendimentos" > 1 for most patients

**For Questions:**
- See COMPREHENSIVE_CODE_ANALYSIS.md for full technical details
- See EXECUTIVE_SUMMARY.md for key patterns and features

---

**Ready for Conversion - Good Luck!**
