"""
Módulo de scraping do sistema PEP (Prontuário Eletrônico do Paciente).

Contém todas as funções necessárias para:
- Configurar o WebDriver
- Fazer login no sistema MV
- Navegar, buscar e selecionar pacientes
- Capturar dados demográficos
"""

import os
import re
import time
import json
from pathlib import Path
from typing import Optional, Dict
from datetime import datetime

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import TimeoutException, NoSuchElementException

from icecream import ic


# ============================================================================
# CONFIGURAÇÃO
# ============================================================================

def setup_icecream():
    """Configura icecream com timestamp"""
    ic.configureOutput(prefix=lambda: f'[{datetime.now().strftime("%H:%M:%S")}] ')


def get_root_path() -> Path:
    """Retorna o caminho raiz do projeto"""
    return Path(__file__).parent.parent


# ============================================================================
# CONFIGURAÇÃO DO DRIVER
# ============================================================================

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


# ============================================================================
# LOGIN
# ============================================================================

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


# ============================================================================
# NAVEGAÇÃO
# ============================================================================

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


# ============================================================================
# BUSCA DE PACIENTE
# ============================================================================

def buscar_paciente(driver: webdriver.Chrome, prontuario: str) -> bool:
    """
    Busca um paciente pelo número de prontuário.

    Args:
        driver: WebDriver do Selenium
        prontuario: Número do prontuário

    Returns:
        True se busca bem-sucedida
    """
    try:
        ic("="*70)
        ic("ETAPA 3: BUSCA DE PACIENTE")
        ic("="*70)
        ic(f"Prontuário: {prontuario}")

        # Localizar campo de pesquisa
        ic("Procurando campo de pesquisa...")

        search_field = None
        selectors = [
            "input[placeholder*='Palavra-chave']",
            "input[placeholder*='palavra-chave']",
            "input[placeholder*='Pesquisar']",
            "input[placeholder*='pesquisar']",
            "input[type='search']",
            "input[name*='search']",
            "input[name*='keyword']",
            "input.search-input",
            "input[formcontrolname*='search']",
            "input[formcontrolname*='keyword']"
        ]

        wait = WebDriverWait(driver, 10)

        for selector in selectors:
            try:
                search_field = wait.until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                )
                ic(f"✓ Campo de pesquisa encontrado: {selector}")
                break
            except:
                continue

        # Fallback heurístico
        if search_field is None:
            ic("⚠️ Tentando localizar qualquer input visível...")
            inputs = driver.find_elements(By.TAG_NAME, "input")
            for inp in inputs:
                if inp.is_displayed():
                    placeholder = inp.get_attribute("placeholder")
                    if placeholder and any(word in placeholder.lower() for word in ['palavra', 'pesquis', 'search', 'busca']):
                        search_field = inp
                        break

        if not search_field:
            ic("⚠️ Campo de pesquisa não encontrado!")
            root = get_root_path()
            driver.save_screenshot(str(root / "errors" / "campo_pesquisa_nao_encontrado.png"))
            return False

        # Preencher campo
        ic(f"Preenchendo prontuário: {prontuario}")
        search_field.clear()
        time.sleep(0.5)
        search_field.send_keys(prontuario)
        time.sleep(1)

        # Procurar botão de pesquisar
        ic("Procurando botão de pesquisar...")
        search_button = None

        button_selectors = [
            "button[type='submit']",
            "button.search-button",
            "button[aria-label*='pesquisar']",
            "button[aria-label*='buscar']",
            ".search-button",
            "//button[contains(text(), 'Pesquisar')]",
            "//button[contains(text(), 'Buscar')]"
        ]

        for selector in button_selectors:
            try:
                if selector.startswith('//'):
                    search_button = driver.find_element(By.XPATH, selector)
                else:
                    search_button = driver.find_element(By.CSS_SELECTOR, selector)

                if search_button and search_button.is_displayed():
                    ic(f"✓ Botão de pesquisar encontrado: {selector}")
                    break
            except:
                continue

        # Submit
        if search_button:
            ic("Clicando no botão pesquisar...")
            search_button.click()
            ic("✓ Botão pesquisar clicado!")
        else:
            ic("⚠️ Botão não encontrado, enviando Enter...")
            search_field.send_keys(Keys.RETURN)

        ic("Aguardando processamento da busca...")
        ic("Aguardando estabilização da página...")

        # Verificar resultados
        try:
            tbody = driver.find_element(By.TAG_NAME, "tbody")
            rows = tbody.find_elements(By.TAG_NAME, "tr")
            visible_rows = [r for r in rows if r.is_displayed() and r.text.strip()]

            if visible_rows:
                ic(f"✓ {len(visible_rows)} resultado(s) encontrado(s)")
            else:
                ic("⚠️ Nenhum resultado visível encontrado")
                root = get_root_path()
                driver.save_screenshot(str(root / "errors" / "sem_resultados.png"))

        except Exception as e:
            ic(f"⚠️ Não foi possível verificar os resultados: {e}")

        ic("✓ Busca concluída e resultados carregados!")
        return True

    except Exception as e:
        ic(f"⚠️ Erro ao buscar paciente: {e}")
        root = get_root_path()
        driver.save_screenshot(str(root / "errors" / "erro_busca_paciente.png"))
        return False


# ============================================================================
# SELEÇÃO DE PACIENTE
# ============================================================================

def selecionar_paciente(driver: webdriver.Chrome, prontuario: Optional[str] = None) -> bool:
    """
    Captura o número do atendimento e navega para a página do paciente.

    Args:
        driver: WebDriver do Selenium
        prontuario: Número do prontuário (opcional, apenas para referência)

    Returns:
        True se seleção bem-sucedida
    """
    try:
        ic("="*70)
        ic("ETAPA 4: SELEÇÃO DO PACIENTE")
        ic("="*70)

        wait = WebDriverWait(driver, 10)

        ic("Aguardando estabilização...")
        time.sleep(3)

        url_base = driver.current_url
        ic(f"URL atual: {url_base}")

        # Procurar número do atendimento
        ic("Procurando número do atendimento...")

        h3_selectors = [
            "//h3[contains(@_ngcontent, '')]",
            "//h3",
            "h3",
            "//table//h3",
            "//tbody//h3",
            "//tr//h3",
        ]

        numero_atendimento = None

        for selector in h3_selectors:
            try:
                if selector.startswith('//'):
                    elements = driver.find_elements(By.XPATH, selector)
                else:
                    elements = driver.find_elements(By.CSS_SELECTOR, selector)

                if not elements:
                    continue

                for element in elements:
                    try:
                        if element.is_displayed():
                            texto = element.text.strip()
                            if texto and texto.replace(' ', '').isdigit():
                                numero_atendimento = texto.replace(' ', '')
                                ic(f"✓ Número do atendimento capturado: {numero_atendimento}")
                                break
                    except:
                        continue

                if numero_atendimento:
                    break

            except:
                continue

        # Fallback: buscar em outros elementos
        if not numero_atendimento:
            ic("⚠️ Número do atendimento não encontrado no h3")
            ic("Tentando encontrar número em outros elementos...")

            try:
                all_elements = driver.find_elements(
                    By.XPATH,
                    "//*[string-length(normalize-space(text())) >= 7 and string-length(normalize-space(text())) <= 10]"
                )

                for element in all_elements:
                    try:
                        if element.is_displayed():
                            texto = element.text.strip()
                            if texto.replace(' ', '').isdigit() and 7 <= len(texto.replace(' ', '')) <= 10:
                                numero_atendimento = texto.replace(' ', '')
                                ic(f"✓ Número encontrado em {element.tag_name}: {numero_atendimento}")
                                break
                    except:
                        continue

            except Exception as e:
                ic(f"⚠️ Erro ao buscar número em outros elementos: {e}")

        if not numero_atendimento:
            ic("⚠️ Não foi possível capturar o número do atendimento")
            root = get_root_path()
            driver.save_screenshot(str(root / "errors" / "numero_nao_encontrado.png"))

            with open(root / "errors" / "page_source.html", "w", encoding="utf-8") as f:
                f.write(driver.page_source)

            return False

        # Construir URL de destino
        ic("Construindo URL de destino...")

        try:
            parts = url_base.split('/#/')
            base_url = parts[0]

            nova_url = f"{base_url}/#/d/3622/MVPEP_LISTA_TODOS_PACIENTES_HTML5/2512/LISTA_TODOS_PACIENTES/h/{numero_atendimento}"

            ic(f"URL de destino: {nova_url}")

            # Navegar
            ic("Navegando para a página do paciente...")
            driver.get(nova_url)

            time.sleep(3)

            # Aguardar loading
            ic("Aguardando página carregar...")
            try:
                wait.until(EC.invisibility_of_element_located((By.CLASS_NAME, "pep-loading-wrapper")))
                ic("✓ Loading desapareceu!")
            except:
                ic("⚠️ Timeout no loading, mas continuando...")

            time.sleep(2)

            url_final = driver.current_url
            ic(f"URL final: {url_final}")

            if numero_atendimento in url_final or '/h/' in url_final:
                ic("✓ Paciente selecionado com sucesso!")
                ic(f"Número do atendimento: {numero_atendimento}")
                return True
            else:
                ic("⚠️ URL final não parece estar correta")
                root = get_root_path()
                driver.save_screenshot(str(root / "errors" / "url_incorreta.png"))
                return False

        except Exception as e:
            ic(f"⚠️ Erro ao construir/navegar para URL: {e}")
            root = get_root_path()
            driver.save_screenshot(str(root / "errors" / "erro_navegacao.png"))
            return False

    except Exception as e:
        ic(f"⚠️ Erro ao selecionar paciente: {e}")
        root = get_root_path()
        driver.save_screenshot(str(root / "errors" / "erro_geral_selecao.png"))
        return False


# ============================================================================
# CAPTURA DE DADOS
# ============================================================================

def capturar_dados_paciente(driver: webdriver.Chrome, prontuario: str) -> Optional[Dict]:
    """
    Captura os dados do paciente da página do PEP.

    Args:
        driver: WebDriver do Selenium
        prontuario: Número do prontuário

    Returns:
        Dicionário com os dados capturados ou None se falhar
    """
    try:
        ic("="*70)
        ic("ETAPA 5: CAPTURA DE DADOS DO PACIENTE")
        ic("="*70)

        wait = WebDriverWait(driver, 10)

        ic("Aguardando página carregar completamente...")
        time.sleep(4)

        # Estrutura de dados
        dados_paciente = {
            "prontuario": prontuario,
            "nome_registro": "",
            "data_nascimento": "",
            "raca": "",
            "cpf": "",
            "codigo_paciente": "",
            "naturalidade": "",
            "data_captura": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

        ic("Iniciando captura de dados do sistema PEP...")

        # ESTRATÉGIA 1: Capturar nome
        ic("[1] Capturando nome do paciente...")
        try:
            nome_element = driver.find_element(
                By.XPATH,
                "//h2[contains(@class, 'mat-card-title') or contains(text(), ' ')]"
            )
            nome_completo = nome_element.text.strip()
            if nome_completo and len(nome_completo) > 5:
                dados_paciente["nome_registro"] = nome_completo
                ic(f"✓ Nome capturado: {nome_completo}")
        except Exception as e:
            ic(f"⚠️ Erro ao capturar nome: {e}")

        # Fallback para nome
        if not dados_paciente["nome_registro"]:
            try:
                elementos_grandes = driver.find_elements(
                    By.XPATH,
                    "//*[contains(@class, 'title') or contains(@class, 'name') or contains(@class, 'paciente')]"
                )
                for elem in elementos_grandes:
                    texto = elem.text.strip()
                    if len(texto) > 10 and ' ' in texto and texto.isupper():
                        dados_paciente["nome_registro"] = texto
                        ic(f"✓ Nome capturado (alternativa): {texto}")
                        break
            except:
                pass

        # ESTRATÉGIA 2: Regex no texto da página
        ic("[2] Analisando texto da página...")
        page_text = driver.find_element(By.TAG_NAME, "body").text

        patterns = {
            "data_nascimento": [
                r'Data de nascimento[:\s]*(\d{2}/\d{2}/\d{4})',
                r'Nascimento[:\s]*(\d{2}/\d{2}/\d{4})',
                r'(\d{2}/\d{2}/\d{4})',
            ],
            "cpf": [
                r'CPF[:\s]*(\d{11})',
                r'CPF[:\s]*(\d{3}\.?\d{3}\.?\d{3}-?\d{2})',
                r'(\d{11})',
            ],
            "codigo_paciente": [
                r'Código do paciente[:\s]*(\d+)',
                r'Código[:\s]*(\d+)',
                r'SAME[:\s]*(\d+)',
            ],
            "raca": [
                r'Raça[:\s]*(\w+)',
                r'Cor[:\s]*(\w+)',
                r'Etnia[:\s]*(\w+)',
            ],
            "naturalidade": [
                r'Naturalidade[:\s]*(\w+)',
                r'Natural de[:\s]*(\w+)',
            ]
        }

        for campo, padroes in patterns.items():
            if not dados_paciente[campo]:
                for padrao in padroes:
                    match = re.search(padrao, page_text, re.IGNORECASE)
                    if match:
                        valor = match.group(1).strip()
                        dados_paciente[campo] = valor
                        ic(f"✓ {campo} capturado via regex: {valor}")
                        break

        # ESTRATÉGIA 3: Pares label-valor
        ic("[3] Procurando estrutura de pares label-valor...")

        xpath_strategies = [
            "//div[contains(text(), ':')]",
            "//span[contains(text(), ':')]",
            "//p[contains(text(), ':')]",
            "//label",
            "//dt",
        ]

        for xpath in xpath_strategies:
            try:
                elementos = driver.find_elements(By.XPATH, xpath)
                for elemento in elementos:
                    try:
                        texto = elemento.text.strip()
                        if ':' in texto:
                            partes = texto.split(':', 1)
                            if len(partes) == 2:
                                label = partes[0].strip().lower()
                                valor = partes[1].strip()

                                # Mapeamento
                                if ('nome' in label or 'registro' in label) and not dados_paciente["nome_registro"]:
                                    if len(valor) > 5:
                                        dados_paciente["nome_registro"] = valor
                                        ic(f"✓ Nome capturado: {valor}")

                                elif ('nascimento' in label or 'nasc' in label) and not dados_paciente["data_nascimento"]:
                                    if re.match(r'\d{2}/\d{2}/\d{4}', valor):
                                        dados_paciente["data_nascimento"] = valor
                                        ic(f"✓ Data de nascimento capturada: {valor}")

                                elif ('raça' in label or 'raca' in label or 'cor' in label) and not dados_paciente["raca"]:
                                    dados_paciente["raca"] = valor
                                    ic(f"✓ Raça capturada: {valor}")

                                elif 'cpf' in label and not dados_paciente["cpf"]:
                                    cpf_limpo = re.sub(r'[^\d]', '', valor)
                                    if len(cpf_limpo) == 11:
                                        dados_paciente["cpf"] = cpf_limpo
                                        ic(f"✓ CPF capturado: {cpf_limpo}")

                                elif ('código' in label or 'codigo' in label or 'same' in label) and not dados_paciente["codigo_paciente"]:
                                    codigo = re.sub(r'[^\d]', '', valor)
                                    if codigo:
                                        dados_paciente["codigo_paciente"] = codigo
                                        ic(f"✓ Código capturado: {codigo}")

                                elif 'naturalidade' in label and not dados_paciente["naturalidade"]:
                                    dados_paciente["naturalidade"] = valor
                                    ic(f"✓ Naturalidade capturada: {valor}")
                    except:
                        continue
            except:
                continue

        # ESTRATÉGIA 4: Campos input
        ic("[4] Verificando campos de input...")
        try:
            inputs = driver.find_elements(By.TAG_NAME, "input")
            for inp in inputs:
                try:
                    value = inp.get_attribute("value")
                    name = (inp.get_attribute("name") or "").lower()
                    id_attr = (inp.get_attribute("id") or "").lower()

                    if not value:
                        continue

                    attrs = name + " " + id_attr

                    if 'nome' in attrs and not dados_paciente["nome_registro"] and len(value) > 5:
                        dados_paciente["nome_registro"] = value
                        ic(f"✓ Nome capturado do input: {value}")

                    elif ('data' in attrs or 'nasc' in attrs) and not dados_paciente["data_nascimento"]:
                        if re.match(r'\d{2}/\d{2}/\d{4}', value):
                            dados_paciente["data_nascimento"] = value
                            ic(f"✓ Data capturada do input: {value}")

                    elif 'cpf' in attrs and not dados_paciente["cpf"]:
                        cpf_limpo = re.sub(r'[^\d]', '', value)
                        if len(cpf_limpo) == 11:
                            dados_paciente["cpf"] = cpf_limpo
                            ic(f"✓ CPF capturado do input: {cpf_limpo}")

                    elif ('raca' in attrs or 'cor' in attrs) and not dados_paciente["raca"]:
                        dados_paciente["raca"] = value
                        ic(f"✓ Raça capturada do input: {value}")

                    elif ('codigo' in attrs or 'same' in attrs) and not dados_paciente["codigo_paciente"]:
                        codigo = re.sub(r'[^\d]', '', value)
                        if codigo:
                            dados_paciente["codigo_paciente"] = codigo
                            ic(f"✓ Código capturado do input: {codigo}")

                    elif 'naturalidade' in attrs and not dados_paciente["naturalidade"]:
                        dados_paciente["naturalidade"] = value
                        ic(f"✓ Naturalidade capturada do input: {value}")
                except:
                    continue
        except Exception as e:
            ic(f"⚠️ Erro ao verificar inputs: {e}")

        # Resumo
        ic("="*70)
        ic("RESUMO DA CAPTURA:")
        ic("="*70)

        dados_capturados = 0
        dados_faltantes = []

        for campo, valor in dados_paciente.items():
            if campo not in ["prontuario", "data_captura"]:
                if valor:
                    ic(f"✓ {campo.replace('_', ' ').title()}: {valor}")
                    dados_capturados += 1
                else:
                    ic(f"✗ {campo.replace('_', ' ').title()}: (não capturado)")
                    dados_faltantes.append(campo)

        ic(f"Total: {dados_capturados}/6 dados capturados")

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


# ============================================================================
# INICIALIZAÇÃO
# ============================================================================

# Configurar icecream ao importar o módulo
setup_icecream()
