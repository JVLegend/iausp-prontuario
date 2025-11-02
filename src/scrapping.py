import os
import time
import json
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select

root = os.getcwd()
root = os.path.dirname(root)

# ============================================================================
# CONFIGURAÇÕES INICIAIS
# ============================================================================

def configurar_driver():
    """Configura e retorna o driver do Selenium"""
    # Get root path of the current code
    root = os.getcwd()
    root = os.path.dirname(root)
    
    # Caminho para o executável do Cent Browser
    cent_path = r"C:\CentBrowser\chrome.exe"
    
    # Caminho para o chromedriver
    driver_path = r"\3rdparty\chromedriver.exe"
    driver_path = os.path.join(root, driver_path.lstrip("\\"))
    print(f"Driver path: {driver_path}")
    
    # Configurar opções do Chrome/Cent Browser
    options = Options()
    options.binary_location = cent_path
    
    # Opções do arquivo .bat
    options.add_argument("--cb-disable-components-auto-update")
    
    # Opções essenciais
    options.add_argument("--start-maximized")
    options.add_argument("--ignore-certificate-errors")
    options.add_argument("--allow-insecure-localhost")
    options.add_argument("--disable-direct-write")
    
    # Adicionar estas opções importantes
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    
    # Desabilitar recursos que podem interferir
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    
    # Configurar o service
    service = Service(executable_path=driver_path)
    
    print("Iniciando o navegador...")
    driver = webdriver.Chrome(service=service, options=options)
    return driver


# ============================================================================
# FUNÇÃO DE LOGIN
# ============================================================================

def fazer_login(driver, usuario, senha, empresa):
    """
    Realiza o login no sistema
    
    Args:
        driver: WebDriver do Selenium
        usuario: Nome de usuário
        senha: Senha
        empresa: Nome da empresa
        
    Returns:
        bool: True se login bem-sucedido, False caso contrário
    """
    try:
        # Navegar para a URL
        url = "http://hishc.phcnet.usp.br"
        print(f"\n{'='*70}")
        print(f"ETAPA 1: LOGIN")
        print(f"{'='*70}")
        print(f"Navegando para: {url}")
        driver.get(url)
        
        wait = WebDriverWait(driver, 10)
        
        print(f"URL atual: {driver.current_url}")
        print(f"Título: {driver.title}")
        
        # Aguardar o formulário carregar
        print("\nAguardando formulário de login...")
        username_field = wait.until(
            EC.presence_of_element_located((By.ID, "username"))
        )
        print("✓ Formulário carregado!")
        
        # Preencher o campo de usuário
        print(f"Preenchendo usuário: {usuario}")
        username_field.clear()
        username_field.send_keys(usuario)
        
        # Preencher o campo de senha
        print("Preenchendo senha...")
        password_field = driver.find_element(By.ID, "password")
        password_field.clear()
        password_field.send_keys(senha)
        
        time.sleep(1)
        
        # Selecionar empresa
        print(f"\nSelecionando empresa: {empresa}")
        company_select_element = wait.until(
            EC.presence_of_element_located((By.ID, "companies"))
        )
        
        company_select = Select(company_select_element)
        
        # Listar empresas disponíveis
        print("Empresas disponíveis:")
        for option in company_select.options:
            if option.get_attribute('value'):
                print(f"  - {option.text} (value: {option.get_attribute('value')})")
        
        # Tentar selecionar empresa
        try:
            company_select.select_by_visible_text(empresa)
            print(f"✓ Empresa '{empresa}' selecionada por texto!")
        except:
            try:
                company_select.select_by_value(empresa)
                print(f"✓ Empresa '{empresa}' selecionada por value!")
            except:
                for option in company_select.options:
                    if empresa.upper() in option.text.upper():
                        company_select.select_by_visible_text(option.text)
                        print(f"✓ Empresa '{option.text}' selecionada!")
                        break
        
        selected_option = company_select.first_selected_option
        print(f"Empresa atualmente selecionada: {selected_option.text}")
        
        time.sleep(1)
        
        # Submeter o formulário
        print("\nSubmetendo formulário...")
        submit_button = driver.find_element(By.CSS_SELECTOR, "input.btn-submit[type='submit']")
        submit_button.click()
        
        # Aguardar o login processar
        print("Aguardando login processar...")
        time.sleep(5)
        
        print(f"\nURL atual: {driver.current_url}")
        print(f"Título: {driver.title}")
        
        # Verificar se o login foi bem-sucedido
        if "login" in driver.current_url.lower():
            print("\n⚠ AVISO: Ainda na página de login!")
            print("Verifique se as credenciais estão corretas.")
            
            try:
                error_elements = driver.find_elements(By.CSS_SELECTOR, ".error, .alert, .message, .error-message")
                for error in error_elements:
                    if error.text.strip():
                        print(f"Mensagem de erro: {error.text}")
            except:
                pass
            
            driver.save_screenshot(f"{root}/errors/erro_login.png")
            print(f"Screenshot salvo em: {root}/errors/erro_login.png")
            return False
        else:
            print("\n✓ Login realizado com sucesso!")
            return True
            
    except Exception as e:
        print(f"\n⚠ Erro no login: {e}")
        import traceback
        traceback.print_exc()
        driver.save_screenshot(f"{root}/errors/erro_login_exception.png")
        return False


# ============================================================================
# FUNÇÃO DE NAVEGAÇÃO
# ============================================================================

def navegar_para_pagina(driver, url):
    """
    Navega para uma URL específica e aguarda carregamento
    
    Args:
        driver: WebDriver do Selenium
        url: URL de destino
        
    Returns:
        bool: True se navegação bem-sucedida
    """
    try:
        print(f"\n{'='*70}")
        print(f"ETAPA 2: NAVEGAÇÃO")
        print(f"{'='*70}")
        print(f"Acessando: {url}")
        driver.get(url)
        
        wait = WebDriverWait(driver, 20)
        
        # Aguardar loading desaparecer
        print("\nAguardando página carregar...")
        try:
            wait.until(EC.invisibility_of_element_located((By.CLASS_NAME, "pep-loading-wrapper")))
            print("✓ Loading desapareceu!")
        except:
            print("⚠ Timeout no loading, mas continuando...")
        
        time.sleep(2)
        
        print(f"URL atual: {driver.current_url}")
        print(f"Título: {driver.title}")
        
        print("\n✓ Navegação concluída!")
        return True
        
    except Exception as e:
        print(f"\n⚠ Erro na navegação: {e}")
        import traceback
        traceback.print_exc()
        driver.save_screenshot(f"{root}/errors/erro_navegacao.png")
        return False


# ============================================================================
# FUNÇÃO DE BUSCA DE PACIENTE
# ============================================================================

def buscar_paciente(driver, prontuario):
    """
    Busca um paciente pelo número de prontuário
    
    Args:
        driver: WebDriver do Selenium
        prontuario: Número do prontuário
        
    Returns:
        bool: True se busca bem-sucedida
    """
    try:
        print(f"\n{'='*70}")
        print(f"ETAPA 3: BUSCA DE PACIENTE")
        print(f"{'='*70}")
        print(f"Buscando prontuário: {prontuario}")
        
        wait = WebDriverWait(driver, 10)
        
        # Lista de seletores possíveis para o campo de busca
        seletores_busca = [
            "input[placeholder*='prontuário' i]",
            "input[placeholder*='paciente' i]",
            "input[placeholder*='busca' i]",
            "input[type='search']",
            "input.search-input",
            "input#searchInput",
            "input[name*='search' i]",
            "//input[contains(@placeholder, 'prontuário')]",
            "//input[contains(@placeholder, 'paciente')]",
            "//input[@type='search']",
        ]
        
        campo_busca = None
        
        print("\nProcurando campo de busca...")
        for i, seletor in enumerate(seletores_busca):
            try:
                print(f"  Tentativa {i+1}: {seletor[:50]}...")
                
                if seletor.startswith('//'):
                    elemento = wait.until(EC.presence_of_element_located((By.XPATH, seletor)))
                else:
                    elemento = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, seletor)))
                
                if elemento.is_displayed() and elemento.is_enabled():
                    campo_busca = elemento
                    print(f"  ✓ Campo encontrado com: {seletor[:50]}")
                    break
                    
            except Exception as e:
                print(f"    Falhou: {str(e)[:50]}")
                continue
        
        if not campo_busca:
            print("\n⚠ Campo de busca não encontrado!")
            
            print("\nTentando encontrar qualquer input visível...")
            try:
                inputs = driver.find_elements(By.TAG_NAME, "input")
                for inp in inputs:
                    if inp.is_displayed() and inp.is_enabled():
                        tipo = inp.get_attribute('type')
                        placeholder = inp.get_attribute('placeholder')
                        print(f"  - Input encontrado: type={tipo}, placeholder={placeholder}")
                        
                        if tipo in ['text', 'search'] or placeholder:
                            campo_busca = inp
                            print(f"  ✓ Usando este input!")
                            break
            except Exception as e:
                print(f"  Erro: {e}")
            
            if not campo_busca:
                driver.save_screenshot(f"{root}/errors/campo_busca_nao_encontrado.png")
                return False
        
        # Limpar e preencher o campo
        print(f"\nPreenchendo campo de busca com: {prontuario}")
        campo_busca.clear()
        time.sleep(0.5)
        campo_busca.send_keys(prontuario)
        time.sleep(1)
        campo_busca.send_keys(Keys.RETURN)
        
        print("Aguardando resultados...")
        time.sleep(3)
        
        # Aguardar loading desaparecer
        try:
            wait.until(EC.invisibility_of_element_located((By.CLASS_NAME, "pep-loading-wrapper")))
            print("✓ Loading desapareceu!")
        except:
            print("⚠ Timeout no loading")
        
        time.sleep(2)
        
        print("\n✓ Busca concluída!")
        return True
        
    except Exception as e:
        print(f"\n⚠ Erro na busca: {e}")
        import traceback
        traceback.print_exc()
        driver.save_screenshot(f"{root}/errors/erro_busca.png")
        return False


# ============================================================================
# FUNÇÃO DE SELEÇÃO DE PACIENTE
# ============================================================================

def selecionar_paciente(driver, prontuario):
    """
    Seleciona o paciente da lista de resultados
    
    Args:
        driver: WebDriver do Selenium
        prontuario: Número do prontuário para validação
        
    Returns:
        bool: True se seleção bem-sucedida
    """
    try:
        print(f"\n{'='*70}")
        print(f"ETAPA 4: SELEÇÃO DE PACIENTE")
        print(f"{'='*70}")
        
        wait = WebDriverWait(driver, 10)
        url_base = driver.current_url
        
        # Aguardar resultados aparecerem
        time.sleep(2)
        
        # Capturar número do atendimento do h3
        print("\nProcurando número do atendimento no h3...")
        
        seletores_h3 = [
            "h3",
            ".result-item h3",
            ".patient-item h3",
            "//h3",
            "div h3",
            "tr h3",
        ]
        
        numero_atendimento = None
        
        for seletor in seletores_h3:
            try:
                print(f"  Tentando: {seletor}...")
                
                if seletor.startswith('//'):
                    elements = driver.find_elements(By.XPATH, seletor)
                else:
                    elements = driver.find_elements(By.CSS_SELECTOR, seletor)
                
                if not elements:
                    print(f"  Nenhum elemento encontrado")
                    continue
                
                print(f"  Encontrados {len(elements)} elemento(s) h3")
                
                # Procurar h3 visível com número
                for i, element in enumerate(elements):
                    try:
                        if element.is_displayed():
                            texto = element.text.strip()
                            print(f"  [{i}] Texto do h3: '{texto}'")
                            
                            # Verificar se contém apenas números
                            if texto and texto.replace(' ', '').isdigit():
                                numero_atendimento = texto.replace(' ', '')
                                print(f"✓ Número do atendimento capturado: {numero_atendimento}")
                                break
                                
                    except Exception as e:
                        print(f"    Erro no elemento h3 [{i}]: {str(e)[:50]}")
                        continue
                
                if numero_atendimento:
                    break
                    
            except Exception as e:
                print(f"  Falhou: {str(e)[:100]}")
                continue
        
        if not numero_atendimento:
            print("⚠ Número do atendimento não encontrado no h3")
            
            # Tentar encontrar em outros elementos
            print("\nTentando encontrar número em outros elementos...")
            
            try:
                # Procurar qualquer elemento com número de 7-8 dígitos
                all_elements = driver.find_elements(By.XPATH, "//*[string-length(normalize-space(text())) >= 7 and string-length(normalize-space(text())) <= 10]")
                
                for element in all_elements:
                    try:
                        if element.is_displayed():
                            texto = element.text.strip()
                            # Verificar se é um número com 7-10 dígitos
                            if texto.replace(' ', '').isdigit() and 7 <= len(texto.replace(' ', '')) <= 10:
                                numero_atendimento = texto.replace(' ', '')
                                print(f"✓ Número encontrado em {element.tag_name}: {numero_atendimento}")
                                break
                    except:
                        continue
                        
            except Exception as e:
                print(f"⚠ Erro ao buscar número em outros elementos: {e}")
        
        if not numero_atendimento:
            print("⚠ Não foi possível capturar o número do atendimento")
            driver.save_screenshot(f"{root}/errors/numero_nao_encontrado.png")
            
            # Salvar HTML para debug
            with open(f"{root}/errors/page_source.html", "w", encoding="utf-8") as f:
                f.write(driver.page_source)
            print("HTML da página salvo em: errors/page_source.html")
            
            return False
        
        # Construir URL de destino
        print(f"\nConstruindo URL de destino...")
        
        try:
            # Parse da URL atual
            parts = url_base.split('/#/')
            base_url = parts[0]
            
            # Construir nova URL
            nova_url = f"{base_url}/#/d/3622/MVPEP_LISTA_TODOS_PACIENTES_HTML5/2512/LISTA_TODOS_PACIENTES/h/{numero_atendimento}"
            
            print(f"URL de destino: {nova_url}")
            
            # Navegar para a URL
            print(f"\nNavegando para a página do paciente...")
            driver.get(nova_url)
            
            # Aguardar carregamento
            time.sleep(3)
            
            # Aguardar loading desaparecer
            print("\nAguardando página carregar...")
            try:
                wait.until(EC.invisibility_of_element_located((By.CLASS_NAME, "pep-loading-wrapper")))
                print("✓ Loading desapareceu!")
            except:
                print("⚠ Timeout no loading, mas continuando...")
            
            time.sleep(2)
            
            # Verificar URL final
            url_final = driver.current_url
            print(f"URL final: {url_final}")
            
            # Verificar se chegou na página correta
            if numero_atendimento in url_final or '/h/' in url_final:
                print(f"\n✓ Paciente selecionado com sucesso!")
                print(f"Número do atendimento: {numero_atendimento}")
                return True
            else:
                print(f"\n⚠ URL final não parece estar correta")
                print(f"Esperado: número {numero_atendimento} ou '/h/' na URL")
                driver.save_screenshot(f"{root}/errors/url_incorreta.png")
                return False
                
        except Exception as e:
            print(f"⚠ Erro ao construir/navegar para URL: {e}")
            import traceback
            traceback.print_exc()
            driver.save_screenshot(f"{root}/errors/erro_navegacao.png")
            return False
        
    except Exception as e:
        print(f"\n⚠ Erro ao selecionar paciente: {e}")
        import traceback
        traceback.print_exc()
        driver.save_screenshot(f"{root}/errors/erro_geral_selecao.png")
        return False


# ============================================================================
# FUNÇÃO DE CAPTURA DE DADOS DO PACIENTE
# ============================================================================

def capturar_dados_paciente(driver, prontuario):
    """
    Captura os dados do paciente da página e salva em JSON
    
    Args:
        driver: WebDriver do Selenium
        prontuario: Número do prontuário
        
    Returns:
        dict: Dicionário com os dados capturados ou None se falhar
    """
    try:
        print(f"\n{'='*70}")
        print(f"ETAPA 5: CAPTURA DE DADOS DO PACIENTE")
        print(f"{'='*70}")
        
        wait = WebDriverWait(driver, 10)
        
        # Aguardar página estar completamente carregada
        time.sleep(3)
        
        # Dicionário para armazenar os dados
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
        
        print("\nIniciando captura de dados...")
        
        # Mapeamento de labels para os campos que queremos capturar
        campos_mapeamento = {
            "nome": ["nome_registro", "nome"],
            "data de nascimento": ["data_nascimento", "dt. nascimento", "nascimento"],
            "raça": ["raca", "cor", "etnia"],
            "cpf": ["cpf"],
            "código": ["codigo_paciente", "cod. paciente", "código paciente"],
            "naturalidade": ["naturalidade", "natural de"]
        }
        
        # Tentar múltiplas estratégias de captura
        
        # ESTRATÉGIA 1: Procurar por labels e seus valores adjacentes
        print("\n[Estratégia 1] Procurando por labels e valores...")
        try:
            # Procurar todos os elementos de texto visíveis
            elementos_texto = driver.find_elements(By.XPATH, "//*[normalize-space(text())]")
            
            for elemento in elementos_texto:
                try:
                    if not elemento.is_displayed():
                        continue
                    
                    texto = elemento.text.strip().lower()
                    
                    # Verificar se o texto corresponde a algum label que queremos
                    for campo_chave, variacoes in campos_mapeamento.items():
                        for variacao in variacoes:
                            if variacao in texto and ":" in texto:
                                # Tentar extrair o valor após os dois pontos
                                partes = elemento.text.split(":")
                                if len(partes) >= 2:
                                    valor = ":".join(partes[1:]).strip()
                                    
                                    # Mapear para o campo correto
                                    if "nome" in variacao and not dados_paciente["nome_registro"]:
                                        dados_paciente["nome_registro"] = valor
                                        print(f"  ✓ Nome capturado: {valor}")
                                    elif "nascimento" in variacao and not dados_paciente["data_nascimento"]:
                                        dados_paciente["data_nascimento"] = valor
                                        print(f"  ✓ Data de nascimento capturada: {valor}")
                                    elif "raça" in variacao or "cor" in variacao and not dados_paciente["raca"]:
                                        dados_paciente["raca"] = valor
                                        print(f"  ✓ Raça capturada: {valor}")
                                    elif "cpf" in variacao and not dados_paciente["cpf"]:
                                        dados_paciente["cpf"] = valor
                                        print(f"  ✓ CPF capturado: {valor}")
                                    elif "código" in variacao or "codigo" in variacao and not dados_paciente["codigo_paciente"]:
                                        dados_paciente["codigo_paciente"] = valor
                                        print(f"  ✓ Código capturado: {valor}")
                                    elif "naturalidade" in variacao and not dados_paciente["naturalidade"]:
                                        dados_paciente["naturalidade"] = valor
                                        print(f"  ✓ Naturalidade capturada: {valor}")
                                    
                except Exception as e:
                    continue
        except Exception as e:
            print(f"  Erro na estratégia 1: {e}")
        
        # ESTRATÉGIA 2: Procurar por estruturas de tabelas ou divs com label/valor
        print("\n[Estratégia 2] Procurando em estruturas de tabela...")
        try:
            # Procurar por pares td/th em tabelas
            tabelas = driver.find_elements(By.TAG_NAME, "table")
            for tabela in tabelas:
                linhas = tabela.find_elements(By.TAG_NAME, "tr")
                for linha in linhas:
                    try:
                        colunas = linha.find_elements(By.TAG_NAME, "td")
                        if len(colunas) >= 2:
                            label = colunas[0].text.strip().lower()
                            valor = colunas[1].text.strip()
                            
                            if "nome" in label and not dados_paciente["nome_registro"]:
                                dados_paciente["nome_registro"] = valor
                                print(f"  ✓ Nome capturado da tabela: {valor}")
                            elif "nascimento" in label and not dados_paciente["data_nascimento"]:
                                dados_paciente["data_nascimento"] = valor
                                print(f"  ✓ Data de nascimento capturada da tabela: {valor}")
                            elif "raça" in label or "cor" in label and not dados_paciente["raca"]:
                                dados_paciente["raca"] = valor
                                print(f"  ✓ Raça capturada da tabela: {valor}")
                            elif "cpf" in label and not dados_paciente["cpf"]:
                                dados_paciente["cpf"] = valor
                                print(f"  ✓ CPF capturado da tabela: {valor}")
                            elif "código" in label or "codigo" in label and not dados_paciente["codigo_paciente"]:
                                dados_paciente["codigo_paciente"] = valor
                                print(f"  ✓ Código capturado da tabela: {valor}")
                            elif "naturalidade" in label and not dados_paciente["naturalidade"]:
                                dados_paciente["naturalidade"] = valor
                                print(f"  ✓ Naturalidade capturada da tabela: {valor}")
                    except:
                        continue
        except Exception as e:
            print(f"  Erro na estratégia 2: {e}")
        
        # ESTRATÉGIA 3: Procurar por inputs/spans com IDs ou classes relevantes
        print("\n[Estratégia 3] Procurando por inputs e spans com IDs/classes...")
        try:
            # Procurar inputs
            inputs = driver.find_elements(By.TAG_NAME, "input")
            for inp in inputs:
                try:
                    id_attr = inp.get_attribute("id") or ""
                    name_attr = inp.get_attribute("name") or ""
                    value = inp.get_attribute("value") or ""
                    
                    atributos = (id_attr + " " + name_attr).lower()
                    
                    if "nome" in atributos and value and not dados_paciente["nome_registro"]:
                        dados_paciente["nome_registro"] = value
                        print(f"  ✓ Nome capturado do input: {value}")
                    elif "nascimento" in atributos and value and not dados_paciente["data_nascimento"]:
                        dados_paciente["data_nascimento"] = value
                        print(f"  ✓ Data de nascimento capturada do input: {value}")
                    elif ("raça" in atributos or "cor" in atributos or "raca" in atributos) and value and not dados_paciente["raca"]:
                        dados_paciente["raca"] = value
                        print(f"  ✓ Raça capturada do input: {value}")
                    elif "cpf" in atributos and value and not dados_paciente["cpf"]:
                        dados_paciente["cpf"] = value
                        print(f"  ✓ CPF capturado do input: {value}")
                    elif ("codigo" in atributos or "código" in atributos) and value and not dados_paciente["codigo_paciente"]:
                        dados_paciente["codigo_paciente"] = value
                        print(f"  ✓ Código capturado do input: {value}")
                    elif "naturalidade" in atributos and value and not dados_paciente["naturalidade"]:
                        dados_paciente["naturalidade"] = value
                        print(f"  ✓ Naturalidade capturada do input: {value}")
                except:
                    continue
        except Exception as e:
            print(f"  Erro na estratégia 3: {e}")
        
        # Verificar quais dados foram capturados
        print("\n" + "="*70)
        print("RESUMO DA CAPTURA:")
        print("="*70)
        dados_capturados = 0
        dados_faltantes = []
        
        for campo, valor in dados_paciente.items():
            if campo not in ["prontuario", "data_captura"]:
                if valor:
                    print(f"✓ {campo}: {valor}")
                    dados_capturados += 1
                else:
                    print(f"✗ {campo}: (não capturado)")
                    dados_faltantes.append(campo)
        
        print(f"\nTotal: {dados_capturados}/6 dados capturados")
        
        # Salvar JSON
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"paciente_{prontuario}_{timestamp}.json"
        filepath = os.path.join(root, "dados_pacientes", filename)
        
        # Criar diretório se não existir
        os.makedirs(os.path.join(root, "dados_pacientes"), exist_ok=True)
        
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(dados_paciente, f, ensure_ascii=False, indent=4)
        
        print(f"\n✓ Dados salvos em: {filepath}")
        
        # Se faltaram dados, salvar HTML para debug
        if dados_faltantes:
            print(f"\n⚠ Dados não capturados: {', '.join(dados_faltantes)}")
            html_filename = f"page_source_{prontuario}_{timestamp}.html"
            html_filepath = os.path.join(root, "dados_pacientes", html_filename)
            
            with open(html_filepath, "w", encoding="utf-8") as f:
                f.write(driver.page_source)
            
            print(f"HTML da página salvo para debug em: {html_filepath}")
            
            # Salvar screenshot
            screenshot_filename = f"screenshot_{prontuario}_{timestamp}.png"
            screenshot_filepath = os.path.join(root, "dados_pacientes", screenshot_filename)
            driver.save_screenshot(screenshot_filepath)
            print(f"Screenshot salvo em: {screenshot_filepath}")
        
        return dados_paciente
        
    except Exception as e:
        print(f"\n⚠ Erro ao capturar dados: {e}")
        import traceback
        traceback.print_exc()
        driver.save_screenshot(f"{root}/errors/erro_captura_dados.png")
        return None


# ============================================================================
# CÓDIGO PRINCIPAL
# ============================================================================

def main():
    """Função principal que executa todo o fluxo"""
    
    # Configurações
    USUARIO = "matheus.galvao"
    SENHA = "Gimb1994!!!"
    EMPRESA = "ICHC"
    URL_DESTINO = "http://bal-pep.phcnet.usp.br/mvpep/5/pt-BR/#/d/141"
    PRONTUARIO = "92570653"
    
    driver = None
    
    try:
        # Configurar driver
        driver = configurar_driver()
        
        # Etapa 1: Fazer login
        if not fazer_login(driver, USUARIO, SENHA, EMPRESA):
            print("\n❌ Falha no login. Encerrando...")
            return
        
        # Etapa 2: Navegar para página específica
        if not navegar_para_pagina(driver, URL_DESTINO):
            print("\n❌ Falha na navegação. Encerrando...")
            return
        
        # Etapa 3: Buscar paciente
        if not buscar_paciente(driver, PRONTUARIO):
            print("\n❌ Falha na busca. Encerrando...")
            return
        
        # Etapa 4: Selecionar paciente
        if not selecionar_paciente(driver, PRONTUARIO):
            print("\n❌ Falha na seleção. Encerrando...")
            return
        
        # Etapa 5: Capturar dados do paciente
        dados = capturar_dados_paciente(driver, PRONTUARIO)
        if not dados:
            print("\n⚠ Falha na captura de dados, mas continuando...")
        
        # Sucesso!
        print(f"\n{'='*70}")
        print("✓✓✓ TODAS AS ETAPAS CONCLUÍDAS COM SUCESSO! ✓✓✓")
        print(f"{'='*70}")
        
        # Manter o navegador aberto
        input("\nPressione Enter para fechar o navegador...")
        
    except Exception as e:
        print(f"\n!!! ERRO GERAL !!!")
        print(f"Erro: {e}")
        import traceback
        traceback.print_exc()
        
        if driver:
            try:
                driver.save_screenshot(f"{root}/errors/erro_geral.png")
                print(f"\nScreenshot salvo em: {root}/errors/erro_geral.png")
            except:
                pass
    
#    finally:
#        if driver:
#            print("\nFechando navegador...")
#            driver.quit()


if __name__ == "__main__":
    main()