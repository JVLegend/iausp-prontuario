# IAUSP Prontuário - Sistema de Extração Automatizada

Sistema de automação web para captura de dados de prontuários médicos do sistema PEP (Prontuário Eletrônico do Paciente) do Hospital das Clínicas - FMUSP.

---

## Índice

1. [Visão Geral](#visão-geral)
2. [Arquitetura do Sistema](#arquitetura-do-sistema)
3. [Fontes de Dados](#fontes-de-dados)
4. [Fluxo de Execução](#fluxo-de-execução)
5. [Estrutura de Arquivos](#estrutura-de-arquivos)
6. [Documentação Técnica](#documentação-técnica)
7. [Instalação e Requisitos](#instalação-e-requisitos)
8. [Estado Atual e Limitações](#estado-atual-e-limitações)
9. [Próximos Passos](#próximos-passos)

---

## Visão Geral

### Objetivo

Automatizar a extração de dados demográficos de pacientes do sistema PEP, reduzindo trabalho manual de aproximadamente **152 horas** para processar 4570 pacientes (estimativa: 2min/paciente manual vs 18s/paciente automatizado).

### Funcionalidades Principais

- ✅ **Login automatizado** no sistema MV Autenticador
- ✅ **Busca de pacientes** por número de prontuário (RGHC)
- ✅ **Captura de dados** demográficos (nome, CPF, data de nascimento, raça, naturalidade)
- ✅ **Salvamento estruturado** em formato JSON
- ✅ **Sistema de debug** com screenshots e HTML para análise de falhas
- ✅ **Anti-detecção** para evitar bloqueio como bot

### Estado Atual

**Status:** Prova de Conceito (PoC) funcional para 1 paciente
- ✅ Todas as etapas testadas e funcionando
- ⚠️ **NÃO está em produção** - processa apenas 1 paciente hardcoded
- ⚠️ Necessita implementação de loop para processar lista completa

---

## Arquitetura do Sistema

### Diagrama de Fluxo

```
[CSV SIGH]
    ↓
[Processamento Pandas] → Listas: Nomes, Matrículas, Datas
    ↓
[Selenium WebDriver]
    ↓
┌─────────────────────────────────────────┐
│ ETAPA 1: Login                          │ → Autenticação MV
├─────────────────────────────────────────┤
│ ETAPA 2: Navegação                      │ → Página de busca
├─────────────────────────────────────────┤
│ ETAPA 3: Busca                          │ → Localizar paciente
├─────────────────────────────────────────┤
│ ETAPA 4: Seleção                        │ → Acessar prontuário
├─────────────────────────────────────────┤
│ ETAPA 5: Captura                        │ → Extrair dados
└─────────────────────────────────────────┘
    ↓
[JSON Output] + [Debug Files]
```

### Tecnologias Utilizadas

| Tecnologia | Versão | Uso |
|-----------|--------|-----|
| Python | 3.7+ | Linguagem base |
| Selenium | 4.0+ | Automação web |
| Pandas | 1.3+ | Processamento CSV |
| Cent Browser | - | Navegador (fork Chromium) |
| ChromeDriver | Compatível | WebDriver |

---

## Fontes de Dados

### 1. Sistema SIGH (Entrada)

**Fonte:** Agenda de consultas realizadas
**Caminho:** AGE > PESQUISA > CONSULTAS REALIZADAS > GERAL

**Filtros aplicados:**
- SERVIÇO = AOFE [+ENTER] **OU** AOFG [+ENTER]
- PÓS-CONSULTA = TRUE
- Data específica

**⚠️ IMPORTANTE:** Exportar como **CSV**, NUNCA XLS

**Estrutura do CSV:**
- 18 colunas
- 4570 linhas (exemplo)
- Encoding: ISO-8859-1
- Campos principais: `MATRÍCULA` (RGHC), `NOME PACIENTE`, `DATA`

### 2. Sistema PEP (MV - Saída)

**Dados extraídos:**

| Campo | Fonte no PEP | Formato |
|-------|-------------|---------|
| Nome Completo | Título da página | MAIÚSCULAS |
| Data de Nascimento | Aba HOME | DD/MM/AAAA |
| Raça/Cor | Aba HOME | String |
| CPF | Aba HOME | 11 dígitos |
| Naturalidade | Aba HOME | Cidade/Estado |
| Código Paciente | Interno | Numérico |

**Dados disponíveis mas NÃO capturados:**
- Diagnósticos (CID) - Aba DIAGNÓSTICOS
- Histórico de atendimentos
- Nome da mãe, CNS, sexo (disponíveis via API - ver seção abaixo)

### 3. API Gateway MV (Descoberta - NÃO utilizada)

**Endpoint:** `http://bal-pep.phcnet.usp.br/mvpep/api/gateway`

**Método:** GET

**Exemplo de resposta:**
```json
{
    "id": 7513022,
    "name": "ALANA MOREIRA PROVAZI",
    "birthDate": "1999-11-13",
    "gender": "FEMALE",
    "mothersName": "MARCIA MARIA ALVES DA SILVA",
    "taxId": "50265757819",
    "cns": "703408277030911",
    "oncologic": false,
    "vip": false,
    "cooperative": false,
    "scientificResearch": false,
    "favorite": false,
    "rghc": "92553023"
}
```

**💡 Oportunidade de Melhoria:** Substituir scraping por chamadas à API (muito mais rápido e confiável).

---

## Fluxo de Execução

### Preparação de Dados (Células 0-2)

#### 1. Carregamento do CSV

```python
# Tratamento especial para CSV mal-formatado
with open(file_path, "r", encoding="iso-8859-1") as f:
    content = f.read().replace(",", " ; ")

data = pd.read_csv(StringIO(content), sep=" ; ", engine='python')
```

**Problema:** CSV contém vírgulas dentro de campos
**Solução:** Substitui vírgulas por ` ; ` e usa como delimitador

#### 2. Limpeza e Extração

```python
# Remove aspas
data = data.replace('"', '', regex=True)

# Extrai listas
nome_paciente_list = [name.upper().strip() for name in data["NOME PACIENTE"]]
matricula_list = [''.join(filter(str.isdigit, mat)) for mat in data["MATRÍCULA"]]
data_list = pd.to_datetime(data["DATA"], format="%d/%m/%Y")
```

**⚠️ Nota:** Estas listas são preparadas mas **não utilizadas** na versão atual.

---

### Automação Web (Células 3-6)

#### ETAPA 1: Configuração do Driver

**Função:** `configurar_driver()`

**Responsabilidades:**
- Localiza ChromeDriver em `3rdparty/chromedriver.exe`
- Configura Cent Browser com opções anti-detecção:
  ```python
  --disable-blink-features=AutomationControlled
  --no-sandbox
  --disable-dev-shm-usage
  ```
- Inicia navegador maximizado

**Output:** Objeto `driver` (WebDriver)

---

#### ETAPA 2: Login

**Função:** `fazer_login(driver, usuario, senha, empresa)`

**Fluxo:**
1. Navega para `http://hishc.phcnet.usp.br`
2. Redireciona para: `http://bal-autentica.phcnet.usp.br/mvautenticador-cas/login`
3. Preenche campos:
   - `#username` ← usuario
   - `#password` ← senha
   - `#companies` (dropdown) ← "ICHC" (ou outra empresa)
4. Submete formulário
5. Aguarda 5s para processamento
6. Verifica sucesso (URL não contém "login")

**Tratamento de Erros:**
- Credenciais inválidas → Screenshot `errors/erro_login.png`
- Timeout → Exception capturada
- Empresa não encontrada → Tenta 3 estratégias de seleção

**⚠️ SEGURANÇA:** Credenciais hardcoded no código (risco!)

---

#### ETAPA 3: Navegação

**Função:** `navegar_para_pagina(driver, url)`

**URL de Destino:** `http://bal-pep.phcnet.usp.br/mvpep/5/pt-BR/#/d/141`

**Comportamento:**
- Acessa URL
- Aguarda **8 segundos** (crítico para aplicação Angular)
- Verifica título da página

**Nota:** Delay fixo é necessário pois página usa carregamento assíncrono.

---

#### ETAPA 4: Busca de Paciente

**Função:** `buscar_paciente(driver, prontuario)`

**Estratégia de Localização (Multi-Seletores):**

Tenta 10+ seletores CSS/XPath para encontrar campo de busca:
```python
selectors = [
    "input[placeholder*='Palavra-chave']",
    "input[type='search']",
    "input[name*='search']",
    # ... mais 7 seletores
]
```

**Fallback Heurístico:**
Se seletores falharem, procura qualquer input visível com placeholder contendo: "palavra", "pesquis", "search", "busca".

**Submit:**
- **Estratégia A:** Localiza e clica botão "Pesquisar"
- **Estratégia B:** Envia `Keys.RETURN` no campo

**Verificação:**
Conta linhas visíveis em `<tbody>` para confirmar resultados.

**Resiliência:** Suporta mudanças na interface HTML.

---

#### ETAPA 5: Seleção do Paciente

**Função:** `selecionar_paciente(driver, prontuario)`

**Lógica:**

1. **Captura número de atendimento:**
   - Busca em elementos `<h3>` visíveis
   - Valida: texto com 7-10 dígitos
   - Fallback: busca em qualquer elemento com texto numérico

2. **Construção da URL:**
   ```python
   base = "http://bal-pep.phcnet.usp.br/mvpep/5/pt-BR"
   nova_url = f"{base}/#/d/3622/MVPEP_LISTA_TODOS_PACIENTES_HTML5/2512/LISTA_TODOS_PACIENTES/h/{numero_atendimento}"
   ```

   **⚠️ Hardcoded:** ID `3622` é fixo (específico do sistema)

3. **Navegação direta:**
   - `driver.get(nova_url)`
   - Aguarda loading Angular desaparecer
   - Verifica URL final contém `/h/` ou número do atendimento

**Tratamento de Falhas:**
- Número não encontrado → Salva HTML e screenshot
- Timeout → Continua mesmo assim

---

#### ETAPA 6: Captura de Dados

**Função:** `capturar_dados_paciente(driver, prontuario)`

**Estrutura de Dados:**
```python
dados_paciente = {
    "prontuario": "92570653",
    "nome_registro": "",
    "data_nascimento": "",
    "raca": "",
    "cpf": "",
    "codigo_paciente": "",
    "naturalidade": "",
    "data_captura": "2025-11-02 14:13:18"
}
```

**4 Estratégias Paralelas de Captura:**

##### Estratégia 1: Captura do Nome Principal

Busca em:
- `<h2 class="mat-card-title">`
- Elementos com classes "title", "name", "paciente"

Critérios:
- Mais de 10 caracteres
- Contém espaços
- Está em MAIÚSCULAS

---

##### Estratégia 2: Regex no Texto da Página

```python
page_text = driver.find_element(By.TAG_NAME, "body").text

patterns = {
    "data_nascimento": [r'Data de nascimento[:\s]*(\d{2}/\d{2}/\d{4})', ...],
    "cpf": [r'CPF[:\s]*(\d{11})', ...],
    "raca": [r'Raça[:\s]*(\w+)', ...],
    # ... mais padrões
}
```

**Lógica:** Padrões específicos primeiro → genéricos depois

**⚠️ Risco:** Regex genérico `(\d{11})` pode capturar número errado.

---

##### Estratégia 3: Parsing Label-Valor

Procura estruturas tipo "Label: Valor":
```python
xpath_strategies = [
    "//div[contains(text(), ':')]",
    "//span[contains(text(), ':')]",
    "//label",
    "//dt",
]
```

Para cada elemento:
```python
texto = "Data de nascimento: 15/03/1985"
label = "data de nascimento"  # lowercase
valor = "15/03/1985"

# Mapeia para campo correspondente
if 'nascimento' in label:
    dados_paciente["data_nascimento"] = valor
```

**Mapeamento inteligente:** Palavras-chave → campos

---

##### Estratégia 4: Valores de Inputs

```python
for inp in driver.find_elements(By.TAG_NAME, "input"):
    value = inp.get_attribute("value")
    attrs = inp.get_attribute("name") + " " + inp.get_attribute("id")

    # Mapeia por atributos
    if 'cpf' in attrs.lower():
        dados_paciente["cpf"] = limpar_cpf(value)
```

**Útil para:** Formulários de edição preenchidos

---

**Consolidação:**

Após as 4 estratégias:
- Conta campos preenchidos vs vazios
- Exibe resumo: `5/6 dados capturados`
- Salva JSON principal
- Se houver falhas: Salva HTML + screenshot para debug

**Exemplo de Output:**
```
======================================================================
RESUMO DA CAPTURA:
======================================================================
✓ nome_registro: LETICIA APARECIDA ROSA DOMINGOS
✓ data_nascimento: 15/03/1985
✓ raca: BRANCA
✓ cpf: 12345678901
✓ codigo_paciente: 2171994
✗ naturalidade: (não capturado)

Total: 5/6 dados capturados

✓ Dados salvos em: dados_pacientes/paciente_92570653_20251024141318.json
✓ HTML salvo para debug em: dados_pacientes/page_source_92570653_20251024141318.html
✓ Screenshot salvo em: dados_pacientes/screenshot_92570653_20251024141318.png
```

---

## Estrutura de Arquivos

```
iausp-prontuario/
├── data/
│   └── AGE_CONS_REAL_RES_20251024_1014.csv    # Input: lista de pacientes do SIGH
│
├── dados_pacientes/                            # Output: JSONs + debug
│   ├── paciente_{prontuario}_{timestamp}.json # ✅ Dados capturados
│   ├── page_source_{prontuario}_{timestamp}.html  # 🐛 HTML (se falha)
│   └── screenshot_{prontuario}_{timestamp}.png    # 🐛 Screenshot (se falha)
│
├── errors/                                     # Screenshots de erro
│   ├── erro_login.png
│   ├── campo_pesquisa_nao_encontrado.png
│   ├── sem_resultados.png
│   ├── numero_nao_encontrado.png
│   └── erro_geral.png
│
├── scripts/
│   └── seleniumwire.ipynb                     # 🔧 Script principal
│
├── 3rdparty/
│   └── chromedriver.exe                       # WebDriver
│
├── TODO.md                                    # Backlog
└── README.md                                  # Este arquivo
```

---

## Documentação Técnica

### Configuração do Navegador

**Opções Críticas do Chrome:**
```python
options.add_argument("--disable-blink-features=AutomationControlled")
options.add_experimental_option("excludeSwitches", ["enable-automation"])
options.add_experimental_option('useAutomationExtension', False)
```

**Propósito:** Remover indicadores de que é um bot.

---

### Estratégia de Waits

| Local | Tipo | Duração | Motivo |
|-------|------|---------|--------|
| Após login | `sleep` | 5s | Processamento servidor |
| Após navegação | `sleep` | 8s | **Crítico:** Carregamento Angular |
| Campo de busca | `WebDriverWait` | 10s | Renderização dinâmica |
| Loading Angular | `WebDriverWait` | 20s | Indicador `.pep-loading-wrapper` |
| Captura de dados | `sleep` | 4s | Renderização completa |

**⚠️ Nota:** Delays fixos (`sleep`) são menos confiáveis que waits explícitos.

---

### Tratamento de Erros

**Estratégia Geral:**
```python
try:
    # Operação
except Exception as e:
    print(f"⚠ Erro: {e}")
    traceback.print_exc()
    driver.save_screenshot("errors/erro_*.png")
    return False  # ou None
```

**Comportamento por Etapa:**

| Etapa | Se Falhar | Ação |
|-------|-----------|------|
| Login | ❌ Encerra | Screenshot + mensagem |
| Navegação | ❌ Encerra | Screenshot + mensagem |
| Busca | ❌ Encerra | Screenshot + mensagem |
| Seleção | ❌ Encerra | Screenshot + HTML |
| Captura | ⚠️ Continua | Salva JSON parcial + debug |

**Logging:**
```
✓ Sucesso
⚠ Aviso (não crítico)
✗ Falha
❌ Falha crítica (encerra)
```

---

### Padrões Regex Utilizados

**Data de Nascimento:**
```python
r'Data de nascimento[:\s]*(\d{2}/\d{2}/\d{4})'  # Específico
r'Nascimento[:\s]*(\d{2}/\d{2}/\d{4})'          # Médio
r'(\d{2}/\d{2}/\d{4})'                          # Genérico (risco!)
```

**CPF:**
```python
r'CPF[:\s]*(\d{11})'                            # Apenas dígitos
r'CPF[:\s]*(\d{3}\.?\d{3}\.?\d{3}-?\d{2})'     # Com formatação
r'(\d{11})'                                     # Genérico (risco!)
```

**Raça:**
```python
r'Raça[:\s]*(\w+)'
r'Cor[:\s]*(\w+)'
```

**⚠️ Limitação:** Padrões genéricos podem capturar dados incorretos.

---

### Volumetria e Performance

**Entrada:**
- 4570 pacientes
- CSV ~2MB

**Saída Estimada:**
- JSONs: 2.3MB
- HTMLs debug (10% falha): 68MB
- Screenshots (10% falha): 46MB
- **Total:** ~116MB

**Tempo:**
- Por paciente: 15-20s
- **Total estimado:** 23 horas contínuas
- Economia vs manual: 152h → 23h = **129 horas economizadas**

---

## Como Usar

### Opção 1: Scripts Python (RECOMENDADO)

Os scripts Python modulares são a **versão recomendada** do sistema, com melhorias em relação ao notebook Jupyter.

**Vantagens:**
- ✅ Carrega múltiplos CSVs automaticamente
- ✅ Loop sobre todos os pacientes
- ✅ Checkpoint system (retoma de onde parou)
- ✅ Rate limiting anti-detecção
- ✅ Logs com timestamps (icecream)
- ✅ Credenciais seguras (.env)

**Guia Rápido:**

1. **Instalar dependências:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configurar credenciais** (criar arquivo `.env`):
   ```bash
   PEP_USUARIO=seu_usuario
   PEP_SENHA=sua_senha
   PEP_EMPRESA=ICHC
   ```

3. **Colocar CSVs** na pasta `data/`:
   ```
   data/
   ├── AGE_CONS_REAL_RES_20251024_1014.csv
   ├── AGE_CONS_REAL_RES_20251025_0900.csv
   └── ... (todos os CSVs do SIGH)
   ```

4. **Executar:**
   ```bash
   python src/main.py
   ```

5. **Modo teste** (recomendado primeiro):
   - O script perguntará: `Processar apenas os primeiros 5 pacientes? (s/N)`
   - Digite `s` para testar com 5 pacientes

6. **Verificar outputs** em `dados_pacientes/`

**Documentação completa:** Ver [QUICK_START.md](QUICK_START.md) e [src/README.md](src/README.md)

---

### Opção 2: Notebook Jupyter (Legado)

O notebook original está em `legado/main.ipynb` (apenas para referência).

**Limitações:**
- ❌ Processa apenas 1 paciente hardcoded
- ❌ Lê apenas 1 CSV por vez
- ❌ Sem checkpoint (perde progresso)
- ❌ Credenciais expostas no código

**Uso (não recomendado para produção):**

1. **Abrir Jupyter:**
   ```bash
   jupyter notebook legado/main.ipynb
   ```

2. **Editar célula de configuração:**
   ```python
   # Célula "Código Principal"
   USUARIO = "seu_usuario"
   SENHA = "sua_senha"
   PRONTUARIO = "12345678"  # Apenas 1 paciente!
   ```

3. **Executar todas as células** (Cell → Run All)

**Nota:** Use esta opção apenas para testes pontuais ou para entender o código original. Para processamento em lote, use os scripts Python.

---

## Instalação e Requisitos

### Requisitos de Sistema

**Hardware:**
- CPU: 2+ cores
- RAM: 4GB mínimo
- Disco: 500MB livres
- Rede: Banda larga estável

**Software:**
- Windows (caminhos hardcoded)
- Python 3.7+
- Cent Browser **OU** Chrome/Chromium
- ChromeDriver compatível com versão do navegador

### Instalação

1. **Clone o repositório:**
   ```bash
   git clone <repo-url>
   cd iausp-prontuario
   ```

2. **Instale dependências:**
   ```bash
   pip install pandas selenium
   ```

3. **Configure ChromeDriver:**
   - Baixe versão compatível: https://chromedriver.chromium.org/
   - Coloque em `3rdparty/chromedriver.exe`

4. **Configure credenciais (TEMPORÁRIO):**
   ```python
   # Em scripts/seleniumwire.ipynb, célula main()
   USUARIO = "seu_usuario"
   SENHA = "sua_senha"
   EMPRESA = "ICHC"
   ```

   **⚠️ TODO:** Migrar para variáveis de ambiente (.env)

5. **Coloque o CSV do SIGH:**
   - Exportar consultas como CSV
   - Salvar em `data/AGE_CONS_REAL_RES_*.csv`
   - Atualizar caminho na célula 1 do notebook

---

## Estado Atual e Limitações

### ✅ O Que Funciona

- ✅ Login automatizado
- ✅ Navegação no sistema PEP
- ✅ Busca de paciente por RGHC
- ✅ Seleção e acesso ao prontuário
- ✅ Captura de 5-6 campos demográficos
- ✅ Salvamento em JSON estruturado
- ✅ Sistema de debug com screenshots/HTML

### ❌ Limitações Críticas

#### 1. **Processa Apenas 1 Paciente**

**Código atual:**
```python
PRONTUARIO = "92570653"  # ❌ Hardcoded

def main():
    # ... login, navegação
    buscar_paciente(driver, PRONTUARIO)  # ❌ Único paciente
    # ... captura
```

**Esperado:**
```python
# ✅ Loop sobre lista de 4570 pacientes
for matricula in matricula_list:
    processar_paciente(driver, matricula)
```

**Impacto:** Sistema inútil para produção sem este loop.

---

#### 2. **Credenciais Expostas**

```python
SENHA = "Gimb1994!!!"  # ❌ RISCO DE SEGURANÇA
```

**Solução necessária:**
```python
import os
from dotenv import load_dotenv

SENHA = os.getenv("PEP_SENHA")  # ✅ Variável de ambiente
```

---

#### 3. **Sem Gestão de Progresso**

**Problemas:**
- Se cair no paciente 3000/4570 → Recomeça do zero
- Não detecta pacientes já processados
- Sem checkpoint/resumo

**Necessário:**
```python
processados = carregar_checkpoint()
for matricula in matriculas:
    if matricula in processados:
        continue
    # ... processar
    salvar_checkpoint(matricula)
```

---

#### 4. **Sem Validação de Dados**

```python
dados_paciente["cpf"] = cpf_limpo  # ❌ Aceita qualquer 11 dígitos
```

**Necessário:**
- Validar dígitos verificadores do CPF
- Validar formato de data (não pode ser futura)
- Validar consistência entre campos

---

#### 5. **IDs Hardcoded**

```python
nova_url = f"{base}/#/d/3622/..."  # ❌ Número mágico
```

**Risco:** Código quebra se estrutura de URLs mudar.

---

#### 6. **Sem Retry Logic**

Se uma operação falhar (timeout, erro de rede):
- ❌ Não tenta novamente
- ❌ Encerra processamento daquele paciente
- ❌ Perde tempo já investido

**Necessário:**
```python
@retry(max_attempts=3, delay=2)
def buscar_paciente(driver, prontuario):
    # ... código
```

---

### ⚠️ Outras Limitações

| Problema | Impacto | Prioridade |
|----------|---------|-----------|
| Timeouts arbitrários | Médio | Baixa |
| Sem rate limiting | Alto (detecção) | Alta |
| Performance subótima | Médio | Média |
| Sem testes unitários | Alto (manutenção) | Média |
| Sem logging estruturado | Médio | Baixa |

---

## Próximos Passos

### Fase 1: Tornar Funcional em Lote (CRÍTICO)

**Prioridade:** 🔴 ALTA

**Tarefas:**

1. **Implementar loop principal** (2h)
   ```python
   def processar_lista_pacientes(driver, matriculas):
       for i, matricula in enumerate(matriculas):
           print(f"[{i+1}/{len(matriculas)}] {matricula}")
           processar_paciente(driver, matricula)
   ```

2. **Externalizar credenciais** (1h)
   - Criar arquivo `.env`
   - Usar `python-dotenv`
   - Adicionar `.env` ao `.gitignore`

3. **Checkpoint system** (3h)
   - Salvar progresso em JSON
   - Detectar pacientes já processados
   - Permitir retomada

**Total:** ~6 horas → **Sistema em produção**

---

### Fase 2: Confiabilidade (IMPORTANTE)

**Prioridade:** 🟡 MÉDIA

**Tarefas:**

1. **Retry logic** (2h)
   - Decorator `@retry`
   - 3 tentativas por padrão
   - Backoff exponencial

2. **Validação de dados** (2h)
   - CPF: Dígitos verificadores
   - Data: Não futura, formato válido
   - Nome: Mínimo 2 palavras

3. **Rate limiting** (1h)
   - Delays aleatórios entre pacientes (5-15s)
   - Evitar detecção como bot

4. **Logging estruturado** (1h)
   - Módulo `logging`
   - Arquivo `scraper.log`
   - Níveis: INFO, WARNING, ERROR

**Total:** ~6 horas → **Sistema robusto**

---

### Fase 3: Migração para API (GAME CHANGER)

**Prioridade:** 🟢 BAIXA (mas alto impacto)

**Descoberta:** Sistema possui API Gateway documentada!

**Endpoint:**
```
http://bal-pep.phcnet.usp.br/mvpep/api/gateway
```

**Vantagens:**
- ✅ 100x mais rápido (ms vs 15s)
- ✅ Dados estruturados (JSON nativo)
- ✅ Sem problemas de mudança de interface
- ✅ Mais confiável
- ✅ Campos adicionais (nome da mãe, CNS, flags)

**Desafios:**
- ❓ Autenticação necessária?
- ❓ Como obter ID do paciente?
- ❓ Rate limiting?

**Investigação necessária:**
1. Reverse engineering das chamadas (DevTools)
2. Documentação de autenticação
3. Endpoints disponíveis

**Estimativa:** 4-8 horas de investigação + 2h implementação

**Impacto:** Redução de 23h → **2h** para processar 4570 pacientes!

---

### Fase 4: Qualidade de Código (MANUTENÇÃO)

**Prioridade:** 🟢 BAIXA

**Tarefas:**

1. **Refatoração OOP** (4h)
   - Classe `PEPScraper`
   - Context manager (`with`)
   - Separação de responsabilidades

2. **Testes unitários** (8h)
   - Pytest
   - Mocks para Selenium
   - Coverage mínimo 70%

3. **Type hints** (2h)
   - Anotações de tipo
   - Mypy para verificação

4. **Documentação** (2h)
   - Docstrings completas
   - Sphinx para gerar docs

**Total:** ~16 horas → **Código manutenível**

---

### Roadmap Resumido

| Fase | Prioridade | Esforço | Benefício |
|------|-----------|---------|-----------|
| 1. Funcional em Lote | 🔴 ALTA | 6h | Sistema utilizável |
| 2. Confiabilidade | 🟡 MÉDIA | 6h | Reduz falhas 80% |
| 3. Migração API | 🟢 BAIXA | 6-10h | **10x mais rápido** |
| 4. Qualidade Código | 🟢 BAIXA | 16h | Facilita manutenção |

**Recomendação:** Executar Fase 1 imediatamente, Fase 2 em paralelo com uso, Fase 3 como próximo projeto.

---

## Notas Finais

### Histórico de Atendimentos Antigos

Para atendimentos pré-transição para MV:

**Sistema:** Prontmed (legado)
**URL:** `http://pdfprontmedmv.phcnet.usp.br/mostrarLaudoProntMed.php?p_atend={codigo_atendimento}`

**Exemplo:**
`http://pdfprontmedmv.phcnet.usp.br/mostrarLaudoProntMed.php?p_atend=4115471`

**⚠️ Limitação:** Necessita código de atendimento (não capturado no fluxo atual).

---

### Dados Disponíveis Não Capturados

**Aba DIAGNÓSTICOS:**
- Códigos CID
- Datas de diagnóstico
- Descrições

**Via API (descoberta):**
- Nome da mãe
- CNS (Cartão Nacional de Saúde)
- Sexo
- Flags: oncológico, VIP, cooperativa, pesquisa científica

**Oportunidade:** Expandir captura para incluir diagnósticos (valor clínico alto).

---

### Considerações Éticas e Legais

⚠️ **IMPORTANTE:**

- Dados de pacientes são **informações sensíveis** (LGPD)
- Uso **exclusivo para fins de pesquisa** aprovada
- **NÃO compartilhar** JSONs ou screenshots
- Adicionar arquivos de dados ao `.gitignore`
- Considerar **anonimização** (hash de CPF/nome)

---

### Contato e Suporte

Para dúvidas ou problemas:
- Ver arquivo `TODO.md` para backlog completo
- Consultar código-fonte: `scripts/seleniumwire.ipynb`
- Análise detalhada disponível no relatório técnico (gerado pela revisão de código)

---

**Última Atualização:** 2025-11-02
**Versão do Código:** Prova de Conceito (PoC)
**Status:** ⚠️ NÃO PRODUÇÃO - Loop principal pendente
