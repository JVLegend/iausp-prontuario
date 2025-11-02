# TODO - IAUSP Prontuário

## ⚠️ LIMITAÇÕES CRÍTICAS (PRIORIDADE ALTA)

### 1. Processa Apenas 1 Paciente
- [ ] **Implementar loop principal** (2h)
  - Código atual: PRONTUARIO hardcoded
  - Necessário: Loop sobre matricula_list (4570 pacientes)
  - Impacto: Sistema INUTILIZÁVEL para produção sem este loop

### 2. Credenciais Expostas (RISCO DE SEGURANÇA)
- [ ] **Externalizar credenciais** (1h)
  - Problema: SENHA hardcoded no código
  - Solução: Criar arquivo `.env` + python-dotenv
  - Adicionar `.env` ao `.gitignore`

### 3. Sem Gestão de Progresso
- [ ] **Implementar checkpoint system** (3h)
  - Problema: Se cair no paciente 3000/4570 → recomeça do zero
  - Necessário: Salvar progresso em JSON
  - Detectar pacientes já processados
  - Permitir retomada

### 4. Sem Validação de Dados
- [ ] **Adicionar validações** (2h)
  - CPF: Validar dígitos verificadores
  - Data: Não pode ser futura, formato válido
  - Nome: Mínimo 2 palavras
  - Problema atual: Aceita qualquer 11 dígitos como CPF válido

### 5. IDs Hardcoded na URL
- [ ] **Tornar IDs dinâmicos** (1h)
  - Problema: ID `3622` hardcoded na URL
  - Risco: Código quebra se estrutura de URLs mudar

### 6. Sem Retry Logic
- [ ] **Implementar retry com backoff** (2h)
  - Problema: Falha em timeout/rede → perde paciente
  - Necessário: Decorator @retry com 3 tentativas
  - Backoff exponencial

**Total Fase 1 (Funcional em Lote):** ~11 horas → Sistema utilizável em produção

---

## 🔧 BACKLOG - Funcionalidades Atuais

### Processamento de Pacientes
- [x] Search Patient
- [x] Open Patient [bugfix aplicado]
- [ ] Extract Patient general metadata (0/6 campos capturados atualmente)
- [ ] Extract Patient medical notes [loop]
- [ ] Save as json (parcialmente - salva mas sem dados)

### Consolidação de Dados
- [ ] Concatenate every 1000 patients into a parquet file

### Refatoração
- [ ] Convert script into a module in .py

---

## 🚀 PRÓXIMOS PASSOS (ROADMAP)

### Fase 2: Confiabilidade (6h) 🟡 MÉDIA PRIORIDADE
- [ ] **Retry logic** (2h) - Decorator @retry, 3 tentativas, backoff exponencial
- [ ] **Rate limiting** (1h) - Delays aleatórios 5-15s entre pacientes
- [ ] **Logging estruturado** (1h) - Módulo logging, arquivo scraper.log
- [ ] **Validação de dados** (2h) - CPF, data, nome

### Fase 3: Migração para API (6-10h) 🟢 BAIXA PRIORIDADE / ALTO IMPACTO
- [ ] **Investigação API Gateway** (4-8h)
  - Endpoint descoberto: `http://bal-pep.phcnet.usp.br/mvpep/api/gateway`
  - Reverse engineering das chamadas (DevTools)
  - Documentação de autenticação
  - Rate limiting da API
- [ ] **Implementação** (2h)
  - Substituir scraping por chamadas API
  - **Impacto:** 23h → 2h para processar 4570 pacientes (10x mais rápido!)

### Fase 4: Qualidade de Código (16h) 🟢 BAIXA PRIORIDADE
- [ ] **Refatoração OOP** (4h) - Classe PEPScraper, context manager
- [ ] **Testes unitários** (8h) - Pytest, mocks, coverage 70%
- [ ] **Type hints** (2h) - Anotações de tipo, mypy
- [ ] **Documentação** (2h) - Docstrings completas, Sphinx

---

## 📋 OTHER STEPS (Longo Prazo)

- [ ] Extract DCM and printouts with metadata to merge with this dataset
- [ ] NAS tool with multiple and incremental backups running daily
- [ ] Deploy Medgemma > Nvidia Spark

---

## 🐛 DEBUG NOTES

### Problemas Conhecidos
- **Múltiplos resultados na busca**: Checar problemas com CPF ou ID contendo os dígitos do RGHC
  - **Solução**: Filtrar e aplicar para usar só a matrícula na busca

- **Flash e captura de evoluções**: Será que o problema no flash vai impedir de capturar as evoluções?

### Taxa de Captura Atual
- **Dados capturados:** 0/6 campos (0% - CRÍTICO!)
- **Etapas funcionando:** Login, navegação, busca, seleção ✅
- **Etapa falhando:** Captura de dados (4 estratégias não funcionaram)

---

## 📊 MÉTRICAS E ESTIMATIVAS

### Volumetria
- **Pacientes totais:** 4570
- **Tempo por paciente:** 15-20s
- **Tempo total estimado:** 23 horas contínuas
- **Economia vs manual:** 152h → 23h = **129 horas economizadas**

### Com Migração para API
- **Tempo estimado:** ~2 horas (10x mais rápido)
- **Taxa de sucesso esperada:** >95% vs ~80% atual

---

## 🗂️ ARQUIVOS LEGADOS

Movidos para pasta `legado/`:
- `main.ipynb` - Versão antiga do script (substituída por seleniumwire.ipynb)
- `erro_geral.png` - Screenshot de erro (documentação visual)

---

**Última Atualização:** 2025-11-02
**Status:** ⚠️ PoC Funcional - NÃO PRODUÇÃO
**Prioridade Imediata:** Fase 1 (Loop + Credenciais + Checkpoint) = 11h
