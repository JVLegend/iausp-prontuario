"""
Script principal para processar múltiplos pacientes do sistema PEP.

Este script:
1. Carrega dados de múltiplos CSVs do SIGH
2. Processa cada paciente em loop
3. Implementa checkpoint system para retomada
4. Salva dados capturados em JSON
"""

import os
import sys
import json
import time
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime

from icecream import ic
from dotenv import load_dotenv

# Imports dos módulos locais
from load_sigh_data import carregar_dados_sigh
from pep_scraper import (
    configurar_driver,
    fazer_login,
    navegar_para_pagina,
    buscar_paciente,
    selecionar_paciente,
    capturar_dados_paciente,
    get_root_path
)


# ============================================================================
# CONFIGURAÇÃO
# ============================================================================

def setup_icecream():
    """Configura icecream com timestamp"""
    ic.configureOutput(prefix=lambda: f'[{datetime.now().strftime("%H:%M:%S")}] ')


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


# ============================================================================
# CHECKPOINT SYSTEM
# ============================================================================

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
        # ic(f"✓ Checkpoint salvo: {len(checkpoint['processados'])} processados")
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


# ============================================================================
# PROCESSAMENTO DE PACIENTE
# ============================================================================

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


# ============================================================================
# LOOP PRINCIPAL
# ============================================================================

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
    import random

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


# ============================================================================
# MAIN
# ============================================================================

def main():
    """Função principal do script"""
    setup_icecream()

    ic("="*70)
    ic("SISTEMA DE CAPTURA DE PRONTUÁRIOS PEP")
    ic("="*70)

    # Carregar credenciais
    ic("Carregando credenciais...")
    credenciais = carregar_credenciais()

    # Carregar dados do SIGH
    ic("Carregando dados do SIGH...")
    df, nomes, matriculas, datas = carregar_dados_sigh()

    if not matriculas:
        ic("❌ Nenhum paciente encontrado para processar!")
        return

    # Confirmar processamento
    print("\n" + "="*70)
    print(f"Total de pacientes a processar: {len(matriculas)}")
    print("="*70)

    # Modo teste ou produção
    resposta = input("\nProcessar apenas os primeiros 5 pacientes? (s/N): ").strip().lower()

    if resposta == 's':
        limite = 5
        ic("⚠️ MODO TESTE: Processando apenas 5 pacientes")
    else:
        limite = None
        resposta_confirma = input(f"\n⚠️ Você está prestes a processar {len(matriculas)} pacientes.\nIsso levará aproximadamente {len(matriculas) * 20 / 3600:.1f} horas.\nContinuar? (s/N): ").strip().lower()

        if resposta_confirma != 's':
            ic("Processamento cancelado pelo usuário")
            return

    # Processar pacientes
    processar_lista_pacientes(
        matriculas=matriculas,
        nomes=nomes,
        credenciais=credenciais,
        limite=limite,
        intervalo_min=5,
        intervalo_max=15
    )

    ic("="*70)
    ic("✓✓✓ SCRIPT CONCLUÍDO ✓✓✓")
    ic("="*70)


if __name__ == "__main__":
    main()
