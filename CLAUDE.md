# CLAUDE.md

Instruções para Claude Code ao trabalhar neste repositório.

## Visão Geral

Sistema automatizado de captura de prontuários médicos do PEP (HCFMUSP) usando Python e Selenium. Processa milhares de registros de pacientes do SIGH.

## Estrutura

```
iausp-prontuario/
├── src/                    # Código Python (RECOMENDADO)
│   ├── load_sigh_data.py  # Carrega CSVs
│   ├── pep_scraper.py     # Scraping com Selenium
│   └── main.py            # Loop principal
├── scripts/               # Jupyter notebooks
│   ├── seleniumwire.ipynb        # Original (legado)
│   └── new_seleniumwire.ipynb    # Nova versão completa
├── data/                  # CSVs do SIGH (input)
└── dados_pacientes/       # JSONs (output, gitignored - LGPD)
```

## Arquivos Principais

- **README.md**: Documentação completa do projeto
- **QUICK_START.md**: Guia rápido de setup (5 min)
- **TODO.md**: Roadmap e backlog
- **requirements.txt**: Dependências Python
- **.env.example**: Template de credenciais

## Regras de Segurança (LGPD)

⚠️ **NUNCA commitar:**
- `.env` (credenciais)
- `dados_pacientes/` (dados de pacientes)
- `checkpoint.json` (identificadores)

## Código e Estilo

- **Logging**: Usar `ic()` (icecream) com timestamps
- **Seletores**: Sempre múltiplos fallbacks (CSS + XPath)
- **Testes**: Sempre testar com 5 pacientes primeiro
- **Erros**: Try/except + screenshots/HTML debug

## Features Principais

1. ✅ **Múltiplos CSVs**: Carrega todos automaticamente
2. ✅ **Loop completo**: Processa todos os pacientes
3. ✅ **Checkpoint**: Retoma de onde parou
4. ✅ **Credenciais seguras**: Arquivo .env
5. ✅ **Rate limiting**: 5-15s entre pacientes
6. ✅ **NOVO**: Captura TODOS os atendimentos (não só o primeiro!)

## Estrutura de Dados

```json
{
  "prontuario": "12345",
  "nome_registro": "NOME",
  "atendimentos": [          // NOVO: Lista de TODOS os atendimentos
    {
      "data_atendimento": "01/10/2025 12:07",
      "especialidade": "OFTALMOLOGIA",
      "diagnostico": "H52.1 - MIOPIA",
      "historico_anamnese": "..."
    }
  ],
  "total_atendimentos": 15   // NOVO: Contador
}
```

## Quick Start

```bash
pip install -r requirements.txt
cp .env.example .env
# Editar .env com credenciais
python src/main.py
```

## Notas Importantes

- Sistema em **produção** - mudanças devem ser conservadoras
- **LGPD compliance** é obrigatório
- **Checkpoint system** é crítico - não quebrar formato
- **Múltiplos seletores** são essenciais para resiliência

---

**Atualização**: 2025-11-02 | **Status**: Produção | **Idioma**: Português (BR)
