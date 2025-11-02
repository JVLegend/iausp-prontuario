# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

This is an automated medical records scraping system for IAUSP (Instituto de Assistência Médica ao Servidor Público Estadual) built with Python and Selenium. The system automates the extraction of patient data from the PEP (Prontuário Eletrônico do Paciente) web interface, processing thousands of patient records from SIGH CSV exports.

## Structure

```
iausp-prontuario/
├── src/                           # Python source code (modular scripts)
│   ├── load_sigh_data.py         # CSV loading and processing
│   ├── pep_scraper.py            # Selenium scraping functions
│   ├── main.py                   # Main execution loop
│   └── README.md                 # Technical documentation
├── scripts/                       # Jupyter notebooks (legacy)
│   └── seleniumwire.ipynb        # Original implementation
├── data/                          # Input CSVs from SIGH
├── dados_pacientes/              # Output JSONs (gitignored - LGPD)
├── legado/                        # Deprecated files
├── .env                          # Credentials (gitignored)
├── checkpoint.json               # Progress tracking (gitignored)
└── requirements.txt              # Python dependencies
```

## Key Files and Workflows

### Core Implementation (Python Scripts - RECOMMENDED)
- **[src/load_sigh_data.py](src/load_sigh_data.py)**: Loads ALL CSVs from `data/` folder automatically, unifies DataFrames, removes duplicates
- **[src/pep_scraper.py](src/pep_scraper.py)**: All scraping functions with anti-detection measures, multiple selector strategies, and icecream logging
- **[src/main.py](src/main.py)**: Main loop with checkpoint system, .env credentials, rate limiting, and resumable processing

### Legacy Implementation (Jupyter Notebook)
- **[scripts/seleniumwire.ipynb](scripts/seleniumwire.ipynb)**: Original single-patient proof of concept
- **Status**: Functional but NOT recommended for production use
- **Limitations**: Only processes 1 hardcoded patient, no checkpoint, exposed credentials

### Configuration Files
- **[.env.example](.env.example)**: Template for credentials configuration
- **[requirements.txt](requirements.txt)**: Python dependencies (pandas, selenium, icecream, python-dotenv, pyarrow)
- **[.gitignore](.gitignore)**: Protects sensitive data (LGPD compliance)

### Documentation
- **[README.md](README.md)**: Complete project documentation with architecture and technical details
- **[QUICK_START.md](QUICK_START.md)**: 5-minute setup guide for new users
- **[TODO.md](TODO.md)**: Backlog, roadmap, known issues, and metrics

## Language and Content

- Primary language: **Portuguese (Brazilian)**
- Technical domain: **Healthcare informatics, web scraping, data processing**
- Security focus: **LGPD compliance** (Brazilian data protection law)

## Important Technical Concepts

### Web Scraping Architecture
- **Selenium WebDriver** with Chrome in headless mode
- **Anti-detection measures**: Disabled automation flags, custom user agent
- **Angular application handling**: Explicit waits for dynamic content loading
- **Multi-strategy data extraction**: 4 parallel strategies (H2 titles, regex, label-value pairs, input fields)
- **Resilient selectors**: Multiple fallback CSS/XPath selectors for each element

### Data Processing
- **CSV encoding**: ISO-8859-1 (SIGH export format)
- **Malformed CSV handling**: Custom parser to handle commas within fields
- **Deduplication**: Based on MATRÍCULA (patient ID) and DATA (date)
- **Output format**: JSON per patient with timestamp

### Key Features
1. **Multiple Atendimentos Capture**: Clicks through ALL items in patient history sidebar, not just the first one
2. **Checkpoint System**: JSON-based progress tracking for resumable processing after interruptions
3. **Rate Limiting**: Random 5-15s delays between patients to avoid bot detection
4. **Secure Credentials**: .env file with python-dotenv (never committed)
5. **Comprehensive Logging**: icecream library with automatic timestamps

### Data Structure (Latest Version)
```json
{
  "prontuario": "92570653",
  "nome_registro": "PATIENT NAME",
  "data_nascimento": "15/03/1985",
  "raca": "BRANCA",
  "cpf": "12345678901",
  "codigo_paciente": "2171994",
  "naturalidade": "SAO PAULO",
  "atendimentos": [
    {
      "data_atendimento": "01/10/2025 12:07",
      "especialidade": "OFTALMOLOGIA",
      "medico": "DR. JOAO SILVA",
      "diagnostico": "H52.1 - MIOPIA",
      "subespecialidade": "RETINA",
      "historico_anamnese": "Patient history...",
      "texto_completo": "Full AMF text...",
      "data_captura": "2025-11-02 14:30:00"
    }
  ],
  "total_atendimentos": 2,
  "data_captura": "2025-11-02 14:30:00"
}
```

## Working with This Repository

### Security and Privacy
- **NEVER commit** `.env` file (contains credentials)
- **NEVER commit** `dados_pacientes/` folder (LGPD protected patient data)
- **NEVER commit** `checkpoint.json` (may contain patient identifiers)
- **ALWAYS use** `.gitignore` rules provided

### Code Style
- **Logging**: Use icecream (`ic()`) for all debug output with timestamps
- **Error handling**: Try/except with fallback strategies, save screenshots/HTML on failure
- **Selectors**: Always provide multiple fallback selectors (CSS + XPath)
- **Waits**: Explicit WebDriverWait, never time.sleep() for element loading

### Testing Workflow
1. Always test with **5 patients first** (modo teste in main.py)
2. Verify JSON outputs in `dados_pacientes/`
3. Check checkpoint.json for success/failure tracking
4. Review screenshots/HTML debug files if any captures failed
5. Only then run full production mode

### Common Issues
- **"0/6 dados capturados"**: Page structure changed, check screenshots and update selectors in `pep_scraper.py`
- **"Campo de pesquisa não encontrado"**: Search input selector changed, add new fallback in `buscar_paciente()`
- **"Número do atendimento não encontrado"**: Patient not found or wrong prontuário format

### Performance Metrics
- **Time per patient**: ~20s (with rate limiting)
- **Total processing time**: ~25 hours for 4570 patients
- **Checkpoint saves**: After each patient (allows resumption)

### Roadmap Priorities
1. ✅ **COMPLETED**: Modular Python scripts, checkpoint system, multiple CSVs, all atendimentos capture
2. 🟡 **MEDIUM**: Data validation (CPF, dates, names), retry logic with backoff
3. 🟢 **LOW**: API migration (10x faster), OOP refactoring, unit tests

## Development Guidelines

When modifying this codebase:

1. **Preserve LGPD compliance**: Never log or display sensitive patient data
2. **Maintain backward compatibility**: Checkpoint format must be loadable by older versions
3. **Update all documentation**: README.md, QUICK_START.md, TODO.md, and src/README.md
4. **Test with modo teste first**: Always verify with 5 patients before full run
5. **Add fallback selectors**: Never rely on single CSS/XPath selector
6. **Use icecream logging**: All functions should have ic() output with descriptive messages

## Quick Start for Developers

```bash
# Setup
pip install -r requirements.txt
cp .env.example .env
# Edit .env with credentials

# Test run (5 patients)
python src/main.py
# Type 's' when prompted

# Full run (all patients)
python src/main.py
# Type 'N' when prompted
```

## Notes for Claude Code

- This is a **production medical data processing system** in active use
- Changes should be **conservative and well-tested**
- Always maintain **LGPD compliance** (Brazilian GDPR equivalent)
- The system processes **real patient data** - treat with appropriate care
- **Icecream logging** is the standard - never use print() statements
- Multiple selector strategies are **critical** for resilience against page structure changes
- The **checkpoint system** is essential - never break its format

---

**Last Updated**: 2025-11-02
**Status**: Production-ready with ongoing improvements
**Primary Use**: Automated extraction of 4570+ patient records from HCFMUSP PEP system
