# EXECUTIVE SUMMARY - Python Scripts Analysis

**Project:** IAUSP Prontuário - Sistema de Extração Automatizada
**Date:** 2025-11-02
**Analysis Scope:** 3 Python modules (1,729 lines total)

---

## QUICK OVERVIEW

The refactored Python scripts represent a **production-ready upgrade** from the original Jupyter notebook, with one **game-changing feature**: **automatic capture of ALL historical attendances per patient** (not just the current one).

**Data Value Multiplier:** 10-20x (from ~1 record per patient to ~10-20 records per patient)

---

## THREE-MODULE ARCHITECTURE

```
[load_sigh_data.py]  →  [main.py]  →  [pep_scraper.py]
   (255 lines)         (379 lines)      (1,095 lines)
       ↓                    ↓                 ↓
   Load CSVs          Orchestrate        Scrape PEP
   Process data       Checkpoint         Extract data
   Unify + clean      Rate limit         Multi-strategy
```

---

## KEY IMPROVEMENTS OVER NOTEBOOK

| Feature | Notebook | Python Scripts |
|---------|----------|----------------|
| CSV Loading | ❌ 1 file hardcoded | ✅ All files auto-discovered |
| Patient Loop | ❌ 1 patient only | ✅ All patients in batch |
| **Attendance Capture** | ❌ **Only 1 (current)** | ✅ **ALL history (10-20+)** |
| Checkpoint | ❌ None | ✅ Resume from interruption |
| Credentials | ❌ Hardcoded | ✅ .env file |
| Rate Limiting | ❌ None | ✅ Random 5-15s delays |
| Logging | ❌ Basic print() | ✅ Icecream with timestamps |
| Error Recovery | ❌ Crash | ✅ Continue + save checkpoint |

---

## CRITICAL INNOVATION: MULTIPLE ATTENDANCES

### What Changed

**Before (Notebook):**
```python
# Only captured the attendance currently displayed
dados_paciente = {
    "prontuario": "12345",
    "nome": "JOAO",
    # ... demographic fields
}
```

**After (Python Scripts):**
```python
# NEW: Captures ALL historical attendances
dados_paciente = {
    "prontuario": "12345",
    "nome": "JOAO",
    # ... demographic fields ...
    "atendimentos": [         # NEW: List of ALL visits
        {
            "data_atendimento": "01/10/2025 12:07",
            "especialidade": "OFTALMOLOGIA",
            "medico": "DR. SILVA",
            "diagnostico": "H52.1 - MIOPIA",
            "subespecialidade": "RETINA",
            "historico_anamnese": "Patient history...",
            "texto_completo": "Full page text...",
        },
        {
            "data_atendimento": "15/09/2025 09:30",
            # ... second attendance ...
        }
        # ... 10-20+ attendances per patient
    ],
    "total_atendimentos": 2
}
```

### How It Works

**Three-Function System:**

1. **clicar_em_todos_atendimentos()** (Lines 533-610, pep_scraper.py)
   - Locates all clickable history items in right sidebar
   - Uses 10+ selector strategies (CSS, XPath, heuristics)
   - Filters for visible and enabled elements
   - Returns: List[WebElement]

2. **capturar_dados_atendimento()** (Lines 613-734, pep_scraper.py)
   - Captures data from ONE attendance (currently displayed)
   - Extracts: date, specialty, doctor, diagnosis, anamnesis
   - Uses regex patterns + multiple strategies
   - Returns: Dict with attendance data

3. **Main Loop in capturar_dados_paciente()** (Lines 764-827, pep_scraper.py)
   ```python
   itens_historico = clicar_em_todos_atendimentos(driver)

   lista_atendimentos = []
   for i, item in enumerate(itens_historico, 1):
       # Scroll to element
       driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", item)

       # Click (with JS fallback)
       try:
           item.click()
       except:
           driver.execute_script("arguments[0].click();", item)

       # Wait for content
       time.sleep(2)

       # Capture THIS attendance
       dados = capturar_dados_atendimento(driver, index=i)
       if dados:
           lista_atendimentos.append(dados)
   ```

---

## COMPLETE FUNCTION INVENTORY

### load_sigh_data.py (255 lines)

| Function | Purpose | Key Feature |
|----------|---------|-------------|
| encontrar_csvs() | Find all CSV files | Auto-discovery in data/ |
| carregar_csv_sigh() | Load one CSV | Special comma handling |
| unificar_dataframes() | Merge CSVs | Deduplication by matricula+date |
| processar_dados_pacientes() | Extract lists | Clean, normalize, validate |
| carregar_dados_sigh() | Main orchestrator | Returns (df, nomes, mats, datas) |
| salvar_dataframe_processado() | Save to disk | Parquet format |

### pep_scraper.py (1,095 lines)

| Function | Purpose | Key Feature |
|----------|---------|-------------|
| configurar_driver() | Setup Selenium | Anti-detection flags |
| fazer_login() | Authenticate | Multi-strategy company selection |
| navegar_para_pagina() | Navigate to URL | Angular wait handling |
| buscar_paciente() | Search patient | 10+ selector fallbacks |
| selecionar_paciente() | Open record | URL construction with number extraction |
| **clicar_em_todos_atendimentos()** | **Find history items** | **NEW: Multi-strategy element location** |
| **capturar_dados_atendimento()** | **Extract ONE attendance** | **NEW: Regex + multiple strategies** |
| **capturar_dados_paciente()** | **Extract patient + ALL attendances** | **NEW: Loop + 4 demographic strategies** |

### main.py (379 lines)

| Function | Purpose | Key Feature |
|----------|---------|-------------|
| carregar_credenciais() | Load .env | Secure credential management |
| carregar_checkpoint() | Load progress | Resume tracking |
| salvar_checkpoint() | Save progress | JSON persistence |
| ja_foi_processado() | Check if done | Skip processed patients |
| processar_paciente() | Process 1 patient | Calls scraper functions |
| processar_lista_pacientes() | Main batch loop | Checkpoint + rate limiting |
| main() | Entry point | User interaction |

---

## DATA FLOW

```
[Multiple CSVs in data/]
         ↓
encontrar_csvs() → Discovers all .csv files
         ↓
carregar_csv_sigh() → Parse each with special handling
         ↓
unificar_dataframes() → Merge + deduplicate
         ↓
processar_dados_pacientes() → Extract clean lists
         ↓
[Lists: nomes[], matriculas[], datas[]]
         ↓
processar_lista_pacientes() → Loop with checkpoint
         ↓
For each patient:
    buscar_paciente() → Search by RGHC
    selecionar_paciente() → Navigate to record
    capturar_dados_paciente() → Extract data
         ↓
         NEW FLOW (multiple attendances):
         clicar_em_todos_atendimentos() → Find history items
         For each history item:
             Click → Wait → capturar_dados_atendimento()
         ↓
         Add lista_atendimentos[] to patient data
         ↓
    [JSON saved: paciente_{prontuario}_{timestamp}.json]
```

---

## IMPLEMENTATION PATTERNS (MUST PRESERVE FOR NOTEBOOK)

### 1. Multi-Strategy Selectors

**Why:** PEP interface changes frequently, Angular dynamic rendering

```python
selectors = [
    "specific.selector",        # Try specific first
    "generic[selector]",        # Then generic
    "//xpath//selector",        # Then XPath
]

element = None
for selector in selectors:
    try:
        element = wait.until(EC.presence_of_element_located(...))
        break
    except:
        continue

# Heuristic fallback
if element is None:
    # Custom logic...
```

### 2. Click with JavaScript Fallback

**Why:** Angular overlays, dynamic z-index

```python
try:
    element.click()
except:
    driver.execute_script("arguments[0].click();", element)
```

### 3. Scroll Before Click

**Why:** Element must be in viewport

```python
driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
time.sleep(0.5)
element.click()
```

### 4. Wait for Loading Indicators

**Why:** Angular async rendering

```python
try:
    WebDriverWait(driver, 5).until(
        EC.invisibility_of_element_located((By.CLASS_NAME, "pep-loading-wrapper"))
    )
except:
    pass  # Continue anyway
```

### 5. Progressive Field Extraction

**Why:** Multiple strategies increase success rate

```python
# Strategy 1: Try specific element
if not dados["campo"]:
    # Strategy 2: Try regex
    if not dados["campo"]:
        # Strategy 3: Try label-value pairs
        if not dados["campo"]:
            # Strategy 4: Try input values
```

---

## CHECKPOINT SYSTEM

**Purpose:** Resume from interruption without losing progress

**File:** checkpoint.json (project root)

**Structure:**
```json
{
    "processados": [
        {"matricula": "12345", "timestamp": "...", "sucesso": true},
        {"matricula": "23456", "timestamp": "...", "sucesso": true}
    ],
    "falhas": [
        {"matricula": "34567", "timestamp": "...", "sucesso": false, "motivo": "..."}
    ],
    "inicio": "2025-11-02T14:00:00",
    "ultima_atualizacao": "2025-11-02T14:32:00"
}
```

**How It Works:**
1. Load checkpoint at start
2. Filter out already processed patients
3. Process remaining patients
4. Update checkpoint after each patient
5. On crash/interrupt: re-run continues from last saved position

---

## ANTI-DETECTION FEATURES

### Browser Configuration
```python
options.add_argument("--disable-blink-features=AutomationControlled")
options.add_experimental_option("excludeSwitches", ["enable-automation"])
options.add_experimental_option('useAutomationExtension', False)
```

### Rate Limiting
```python
# Random delay between patients
intervalo = random.randint(5, 15)  # 5-15 seconds
time.sleep(intervalo)
```

### Realistic Scrolling
```python
driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
time.sleep(0.5)  # Human-like pause
```

---

## PERFORMANCE ESTIMATES

### Input Scale
- CSV files: 3-5 files
- Total patients: ~4,300 (after deduplication)
- Average attendances per patient: 10

### Processing Time

**Old (1 attendance per patient):**
- ~20s per patient
- 4,300 × 20s = 86,000s = **23.9 hours**

**New (10 attendances per patient):**
- ~45s per patient (depends on attendance count)
- 4,300 × 45s = 193,500s = **53.75 hours**

**Trade-off:** 2.25x longer but **10x more data**

### Output Size
- JSON per patient: 5-50KB (depends on attendances)
- Total: ~86MB JSON files
- Debug files (10% failure): ~107MB
- **Total: ~194MB**

---

## RELIABILITY FEATURES

✅ **Checkpoint System** - Survives crashes/interrupts
✅ **Error Screenshots** - Automatic debug capture
✅ **Multi-Strategy Selectors** - Survives UI changes
✅ **JavaScript Fallbacks** - Works with overlays
✅ **Graceful Degradation** - Partial data saved
✅ **Rate Limiting** - Avoids detection/blocking
✅ **Logging** - Icecream with timestamps

---

## SECURITY CONSIDERATIONS

**Credentials:**
- ✅ .env file (not committed)
- ✅ Environment variables
- ⚠️ Plaintext on disk (no encryption)
- ⚠️ Hardcoded fallback in code

**Data Privacy:**
- ❌ No encryption at rest
- ❌ No anonymization
- ✅ .gitignore for data files
- ✅ Local storage only

**⚠️ IMPORTANT:** This captures PHI/PII subject to LGPD. Ensure:
- Approved research protocol
- Ethics committee approval
- Secure handling/storage

---

## JUPYTER NOTEBOOK CONVERSION - CRITICAL CHECKLIST

### MUST PRESERVE

1. ✅ **Multiple attendances capture loop** (lines 764-827, pep_scraper.py)
   - This is the MAIN value-add
   - Do NOT simplify or skip

2. ✅ **clicar_em_todos_atendimentos()** with all selector strategies
   - All 10+ selectors needed for robustness

3. ✅ **JavaScript click fallbacks**
   - Required for Angular overlays

4. ✅ **Scroll before click**
   - Prevents "element not visible" errors

5. ✅ **Wait for loading indicators**
   - Critical for Angular async rendering

6. ✅ **Checkpoint system**
   - Enables resumable processing

7. ✅ **Rate limiting with random delays**
   - Prevents detection

8. ✅ **Debug screenshots/HTML on error**
   - Essential for debugging failures

### RECOMMENDED CELL STRUCTURE

```
Cell 1: Imports + Config
Cell 2: Data Loading Functions (load_sigh_data.py)
Cell 3: Scraping - Setup Functions (driver, login, nav)
Cell 4: Scraping - Patient Functions (search, select)
Cell 5: Scraping - Data Capture (CRITICAL - attendances loop)
Cell 6: Checkpoint Functions
Cell 7: Processing Functions (single + batch)
Cell 8: EXECUTE - Load Data
Cell 9: EXECUTE - Test Mode (1 patient)
Cell 10: EXECUTE - Production Mode (all patients)
Cell 11: ANALYZE - Results
```

### TESTING CHECKLIST

1. ✅ Load CSVs successfully
2. ✅ Configure driver and login
3. ✅ Process 1 patient end-to-end
4. ✅ **Verify multiple attendances captured** (check lista_atendimentos length)
5. ✅ Verify JSON structure correct
6. ✅ Test checkpoint save/load
7. ✅ Test with 5 patients in batch
8. ✅ Verify rate limiting works
9. ✅ Test error recovery (intentional failure)
10. ✅ Verify debug files created on error

---

## EXTENSIBILITY

### Add New Fields to Capture

```python
# In capturar_dados_atendimento()
dados_atendimento["novo_campo"] = ""

patterns["novo_campo"] = [
    r'Label[:\s]*(.+)',
]
```

### Change Rate Limiting

```python
# In main()
processar_lista_pacientes(
    ...,
    intervalo_min=10,  # Increase from 5
    intervalo_max=30   # Increase from 15
)
```

### Add Validation

```python
# Create in load_sigh_data.py
def validar_cpf(cpf: str) -> bool:
    # Implement digit validation
    return True/False
```

---

## FUTURE ENHANCEMENTS

**Priority 1 (HIGH IMPACT):**
- Investigate API migration (100x faster, see README for endpoint)

**Priority 2 (MEDIUM IMPACT):**
- Add data validation pipeline
- Implement retry logic with exponential backoff

**Priority 3 (LOW IMPACT):**
- Parallel processing (3-5 workers)
- Real-time monitoring dashboard

---

## CONCLUSION

The refactored Python scripts are **production-ready** with one game-changing innovation: **automatic capture of ALL historical attendances**. This multiplies data value by 10-20x compared to the original notebook.

**For Jupyter Notebook Conversion:**
- Preserve all 8 critical patterns (see checklist above)
- Follow recommended cell structure
- Test thoroughly, especially multiple attendances capture
- Use test mode (5 patients) before full run

**Key Success Metrics:**
- ✅ All patients processed
- ✅ Average 10+ attendances per patient
- ✅ <10% failure rate
- ✅ Checkpoint system working (can resume)

**Files for Reference:**
- Complete analysis: COMPREHENSIVE_CODE_ANALYSIS.md (1,000+ lines)
- This summary: EXECUTIVE_SUMMARY.md
- Original README: README.md

---

**Analysis Complete - Ready for Notebook Conversion**
