# Código Fonte - IAUSP Prontuário

Esta pasta contém os scripts Python modulares do sistema de captura de prontuários.

## 📁 Estrutura

```
src/
├── load_sigh_data.py    # Módulo de carregamento de CSVs do SIGH
├── pep_scraper.py       # Módulo de scraping do sistema PEP
├── main.py              # Script principal (loop de processamento)
└── README.md            # Este arquivo
```

## 🚀 Como Usar

### 1. Instalação de Dependências

```bash
# Criar ambiente virtual (recomendado)
python -m venv venv

# Ativar ambiente virtual
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Instalar dependências
pip install -r ../requirements.txt
```

### 2. Configuração

Crie um arquivo `.env` na raiz do projeto (copie de `.env.example`):

```bash
PEP_USUARIO=seu_usuario
PEP_SENHA=sua_senha
PEP_EMPRESA=ICHC
PEP_URL=http://bal-pep.phcnet.usp.br/mvpep/5/pt-BR/#/d/141
```

### 3. Preparar Dados

Coloque os arquivos CSV do SIGH na pasta `data/`:

```
data/
├── AGE_CONS_REAL_RES_20251024_1014.csv
├── AGE_CONS_REAL_RES_20251025_0900.csv
└── ... (outros CSVs)
```

### 4. Executar

```bash
# Rodar script principal
python src/main.py
```

O script irá:
1. Perguntar se deseja processar apenas 5 pacientes (modo teste)
2. Carregar todos os CSVs automaticamente
3. Verificar checkpoint de processamentos anteriores
4. Processar cada paciente em sequência
5. Salvar dados em `dados_pacientes/`

## 📝 Módulos

### load_sigh_data.py

Responsável por:
- ✅ Encontrar todos os CSVs na pasta `data/`
- ✅ Carregar e parsear CSVs mal-formatados do SIGH
- ✅ Unificar múltiplos DataFrames
- ✅ Remover duplicatas
- ✅ Processar listas de nomes, matrículas e datas
- ✅ Salvar DataFrame processado em Parquet (opcional)

**Uso standalone:**
```python
from load_sigh_data import carregar_dados_sigh

df, nomes, matriculas, datas = carregar_dados_sigh()
print(f"Total de pacientes: {len(matriculas)}")
```

---

### pep_scraper.py

Módulo com todas as funções de scraping:
- ✅ `configurar_driver()` - Configura Selenium com anti-detecção
- ✅ `fazer_login()` - Login no sistema MV
- ✅ `navegar_para_pagina()` - Navegação com waits para Angular
- ✅ `buscar_paciente()` - Busca por prontuário com múltiplos seletores
- ✅ `selecionar_paciente()` - Captura número de atendimento e navega
- ✅ `capturar_dados_paciente()` - 4 estratégias de extração de dados

**Uso standalone:**
```python
from pep_scraper import configurar_driver, fazer_login, capturar_dados_paciente

driver = configurar_driver()
fazer_login(driver, "usuario", "senha", "ICHC")
# ... navegar, buscar, selecionar
dados = capturar_dados_paciente(driver, "12345678")
```

---

### main.py

Script principal que orquestra todo o fluxo:
- ✅ Carrega credenciais do `.env`
- ✅ Carrega todos os CSVs do SIGH
- ✅ Implementa checkpoint system
- ✅ Loop de processamento com rate limiting
- ✅ Tratamento de erros e interrupções
- ✅ Logs com timestamps (icecream)

**Checkpoint System:**
- Salva progresso em `checkpoint.json`
- Permite retomada após falhas/interrupções
- Não reprocessa pacientes já concluídos

**Rate Limiting:**
- Intervalo aleatório de 5-15s entre pacientes
- Evita detecção como bot

## 🐛 Debugging

Todos os módulos usam **icecream** para logging com timestamps:

```
[14:32:15] ✓ 4570 paciente(s) processado(s)
[14:32:16] Aguardando estabilização...
[14:32:19] ✓ Campo de pesquisa encontrado: input[placeholder*='Palavra-chave']
```

Para desabilitar logs do icecream:
```python
from icecream import ic
ic.disable()
```

## 📊 Outputs

### Dados Capturados
- **Localização:** `dados_pacientes/`
- **Formato:** JSON (um por paciente)
- **Nome:** `paciente_{prontuario}_{timestamp}.json`

### Arquivos de Debug (se captura falhar)
- `page_source_{prontuario}_{timestamp}.html` - HTML da página
- `screenshot_{prontuario}_{timestamp}.png` - Screenshot da interface

### Checkpoint
- **Localização:** Raiz do projeto
- **Arquivo:** `checkpoint.json`
- **Conteúdo:**
  ```json
  {
    "processados": [
      {"matricula": "12345678", "timestamp": "...", "sucesso": true}
    ],
    "falhas": [
      {"matricula": "87654321", "timestamp": "...", "sucesso": false, "motivo": "..."}
    ],
    "inicio": "2025-11-02T14:30:00",
    "ultima_atualizacao": "2025-11-02T15:45:00"
  }
  ```

## ⚠️ Importante

### Segurança
- **NUNCA** commite o arquivo `.env` (credenciais)
- **NUNCA** commite arquivos de `dados_pacientes/` (LGPD)
- Use `.gitignore` fornecido

### Performance
- **Tempo estimado:** ~20s por paciente
- **4570 pacientes:** ~25 horas contínuas
- **Recomendação:** Rodar overnight ou em máquina dedicada

### Falhas Comuns
1. **"Campo de pesquisa não encontrado"**
   - Interface do PEP mudou
   - Adicionar novos seletores em `buscar_paciente()`

2. **"Número do atendimento não encontrado"**
   - Busca não retornou resultados
   - Verificar se prontuário está correto

3. **"0/6 dados capturados"**
   - Estrutura da página mudou
   - Verificar HTML e screenshot em `dados_pacientes/`
   - Ajustar estratégias de captura

## 🔧 Manutenção

### Adicionar Novo Campo de Captura

Editar `pep_scraper.py`, função `capturar_dados_paciente()`:

1. Adicionar campo no dicionário `dados_paciente`
2. Adicionar padrão regex em `patterns` (Estratégia 2)
3. Adicionar mapeamento label-valor (Estratégia 3)
4. Adicionar verificação de input (Estratégia 4)

### Ajustar Rate Limiting

Editar `main.py`, função `processar_lista_pacientes()`:

```python
intervalo_min=10,  # Aumentar para 10s
intervalo_max=30   # Aumentar para 30s
```

## 📚 Referências

- **Documentação completa:** `README.md` (raiz do projeto)
- **TODO e roadmap:** `TODO.md`
- **Arquivos legados:** `legado/`

---

**Última Atualização:** 2025-11-02
**Versão:** 1.0.0 (Python refatorado)
