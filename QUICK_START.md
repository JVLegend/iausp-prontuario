# Guia Rápido de Início

## 🚀 Setup em 5 Minutos

### 1. Instalar Dependências

```bash
pip install -r requirements.txt
```

**Dependências principais:**
- `pandas` - Processamento de CSVs
- `selenium` - Automação web
- `python-dotenv` - Gestão de variáveis de ambiente
- `icecream` - Logging com timestamps
- `pyarrow` - Suporte a Parquet

---

### 2. Configurar Credenciais

Copie o arquivo de exemplo e edite com suas credenciais:

```bash
cp .env.example .env
```

Edite `.env`:
```
PEP_USUARIO=seu_usuario
PEP_SENHA=sua_senha
PEP_EMPRESA=ICHC
```

⚠️ **IMPORTANTE:** Nunca commite o arquivo `.env`!

---

### 3. Preparar CSVs do SIGH

Coloque seus CSVs exportados do SIGH na pasta `data/`:

```
data/
├── AGE_CONS_REAL_RES_20251024_1014.csv
├── AGE_CONS_REAL_RES_20251025_0900.csv
└── ... (todos os CSVs que você tiver)
```

**Dica:** O script carrega **TODOS** os CSVs automaticamente e remove duplicatas.

---

### 4. Executar

```bash
python src/main.py
```

O script vai perguntar:
```
Processar apenas os primeiros 5 pacientes? (s/N):
```

**Recomendação:** Digite `s` para testar com 5 pacientes primeiro!

---

## 📊 O Que Esperar

### Modo Teste (5 pacientes)
- **Tempo:** ~2-3 minutos
- **Output:** 5 arquivos JSON em `dados_pacientes/`
- **Checkpoint:** Salvo em `checkpoint.json`

### Modo Produção (todos os pacientes)
- **Tempo:** ~25 horas para 4570 pacientes
- **Output:** 4570 arquivos JSON
- **Checkpoint:** Atualizado a cada paciente

### Logs Exemplo

```
[14:30:00] ======================================================================
[14:30:00] CARREGAMENTO DE DADOS DO SIGH
[14:30:00] ======================================================================
[14:30:01] Procurando CSVs em: c:\...\data
[14:30:01] ✓ 3 arquivo(s) CSV encontrado(s)
[14:30:02] Carregando: AGE_CONS_REAL_RES_20251024_1014.csv
[14:30:03] ✓ 4570 linhas carregadas
[14:30:04] ✓ 4570 paciente(s) processado(s)
[14:30:05] ======================================================================
[14:30:05] ETAPA 1: LOGIN
[14:30:05] ======================================================================
[14:30:06] Navegando para: http://hishc.phcnet.usp.br
[14:30:08] ✓ Login realizado com sucesso!
[14:30:09] ======================================================================
[14:30:09] [1/5] Processando paciente...
[14:30:09] ======================================================================
[14:30:10] Processando: LETICIA APARECIDA ROSA DOMINGOS (Matrícula: 92570653)
...
```

---

## 🔄 Retomando Após Interrupção

O script **salva automaticamente** o progresso em `checkpoint.json`.

Se o script for interrompido:
1. **Não faça nada!** O checkpoint está salvo
2. Execute novamente: `python src/main.py`
3. O script continuará de onde parou

**Exemplo:**
```
[14:35:00] ✓ Checkpoint carregado: 2350 pacientes já processados
[14:35:01] Total de pacientes: 4570
[14:35:01] Já processados: 2350
[14:35:01] Pendentes: 2220
```

---

## 📁 Estrutura de Outputs

### Dados Capturados

**Localização:** `dados_pacientes/paciente_92570653_20251102_143000.json`

**Estrutura:**
```json
{
    "prontuario": "92570653",
    "nome_registro": "LETICIA APARECIDA ROSA DOMINGOS",
    "data_nascimento": "15/03/1985",
    "raca": "BRANCA",
    "cpf": "12345678901",
    "codigo_paciente": "2171994",
    "naturalidade": "SAO PAULO",
    "data_captura": "2025-11-02 14:30:00"
}
```

### Checkpoint

**Localização:** `checkpoint.json` (raiz do projeto)

**Estrutura:**
```json
{
    "processados": [
        {
            "matricula": "92570653",
            "timestamp": "2025-11-02T14:30:00",
            "sucesso": true
        }
    ],
    "falhas": [],
    "inicio": "2025-11-02T14:00:00",
    "ultima_atualizacao": "2025-11-02T14:30:00"
}
```

---

## ⚠️ Troubleshooting Rápido

### Erro: "ChromeDriver não encontrado"

```bash
# Baixe o ChromeDriver compatível com seu Chrome
# https://chromedriver.chromium.org/
# Coloque em: 3rdparty/chromedriver.exe
```

### Erro: "Credenciais inválidas"

Verifique o arquivo `.env`:
- Usuário está correto?
- Senha está correta?
- Empresa é "ICHC"?

### Erro: "Nenhum CSV encontrado"

```bash
# Verifique se os CSVs estão em data/
ls data/*.csv

# Se não houver CSVs, exporte do SIGH e coloque lá
```

### Erro: "0/6 dados capturados"

Isso significa que a estrutura da página mudou.

**O que fazer:**
1. Verifique o HTML salvo em `dados_pacientes/page_source_*.html`
2. Verifique o screenshot em `dados_pacientes/screenshot_*.png`
3. Reporte o problema ou ajuste os seletores em `pep_scraper.py`

---

## 🎯 Próximos Passos

Após rodar o teste com 5 pacientes:

1. **Verifique os outputs**
   - Abra alguns JSONs em `dados_pacientes/`
   - Confirme que os dados foram capturados

2. **Ajuste se necessário**
   - Taxa de captura baixa? Veja arquivos de debug
   - Muitas falhas? Verifique screenshots

3. **Rode em produção**
   - Execute `python src/main.py`
   - Digite `N` quando perguntar sobre modo teste
   - Deixe rodando (recomendado: overnight)

4. **Monitore o checkpoint**
   - Abra `checkpoint.json` periodicamente
   - Veja quantos foram processados com sucesso

---

## 📚 Documentação Completa

- **README principal:** [README.md](README.md)
- **Código-fonte:** [src/README.md](src/README.md)
- **TODO e roadmap:** [TODO.md](TODO.md)

---

## 🆘 Precisa de Ajuda?

1. Verifique os logs do icecream (com timestamps)
2. Veja screenshots e HTMLs em `dados_pacientes/`
3. Consulte a documentação completa
4. Reporte problemas com screenshots anexados

---

**Boa sorte! 🚀**

**Última Atualização:** 2025-11-02
