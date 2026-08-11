#!/usr/bin/env python3

"""
GitHub Repository Manager
=========================

Lista automaticamente os repositórios do GitHub,
permite selecionar vários pelo número e excluí-los
em uma única operação.

Recursos:
- Lista todos os repositórios
- Paginação automática
- Mostra nome, visibilidade e descrição
- Seleção por números
- Suporta intervalos: 1,3,5-8
- Seleção "todos"
- Dupla confirmação
- Verificação antes da exclusão
- Relatório final
- Não grava o token no código
"""

from __future__ import annotations

import os
import sys
import time
import requests


# ============================================================
# CONFIGURAÇÃO
# ============================================================

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")

API_URL = "https://api.github.com"

PER_PAGE = 100

DELAY_SECONDS = 0.5


# ============================================================
# HEADERS
# ============================================================

HEADERS = {
    "Accept": "application/vnd.github+json",
    "Authorization": f"Bearer {GITHUB_TOKEN}",
    "X-GitHub-Api-Version": "2026-03-10",
}


# ============================================================
# LIMPAR TERMINAL
# ============================================================

def limpar_tela():

    if os.name == "nt":
        os.system("cls")
    else:
        os.system("clear")


# ============================================================
# VERIFICAR CONFIGURAÇÃO
# ============================================================

def verificar_configuracao():

    if not GITHUB_TOKEN:

        print()
        print("ERRO: GITHUB_TOKEN não configurado.")
        print()

        print("Linux / Termux:")
        print('export GITHUB_TOKEN="SEU_TOKEN"')
        print()

        print("Windows PowerShell:")
        print('$env:GITHUB_TOKEN="SEU_TOKEN"')
        print()

        sys.exit(1)


# ============================================================
# TESTAR TOKEN
# ============================================================

def obter_usuario():

    url = f"{API_URL}/user"

    try:

        response = requests.get(
            url,
            headers=HEADERS,
            timeout=30,
        )

    except requests.RequestException as error:

        print(f"Erro de conexão: {error}")
        sys.exit(1)

    if response.status_code != 200:

        print()
        print("ERRO: token inválido ou sem acesso.")
        print()
        print(f"HTTP {response.status_code}")
        print(response.text)
        sys.exit(1)

    return response.json()


# ============================================================
# LISTAR REPOSITÓRIOS
# ============================================================

def listar_repositorios():

    repositorios = []

    page = 1

    print()
    print("Buscando seus repositórios...")
    print()

    while True:

        url = (
            f"{API_URL}/user/repos"
            f"?per_page={PER_PAGE}"
            f"&page={page}"
            f"&affiliation=owner,collaborator,organization_member"
            f"&sort=full_name"
            f"&direction=asc"
        )

        try:

            response = requests.get(
                url,
                headers=HEADERS,
                timeout=30,
            )

        except requests.RequestException as error:

            print(f"Erro de conexão: {error}")
            sys.exit(1)

        if response.status_code != 200:

            print()
            print(
                f"Erro ao buscar repositórios: "
                f"HTTP {response.status_code}"
            )
            print(response.text)
            sys.exit(1)

        dados = response.json()

        if not dados:
            break

        repositorios.extend(dados)

        print(
            f"  Página {page}: "
            f"{len(dados)} repositório(s)"
        )

        if len(dados) < PER_PAGE:
            break

        page += 1

    return repositorios


# ============================================================
# MOSTRAR REPOSITÓRIOS
# ============================================================

def mostrar_repositorios(repositorios):

    print()
    print("=" * 90)
    print("                 SEUS REPOSITÓRIOS")
    print("=" * 90)

    for i, repo in enumerate(repositorios, start=1):

        nome = repo.get("name", "")

        visibilidade = (
            "PRIVADO"
            if repo.get("private")
            else "PÚBLICO"
        )

        descricao = repo.get("description") or ""

        descricao = descricao.replace("\n", " ").strip()

        if len(descricao) > 45:
            descricao = descricao[:42] + "..."

        print(
            f"{i:4d}. "
            f"{nome:<35} "
            f"{visibilidade:<8} "
            f"{descricao}"
        )

    print("=" * 90)
    print(f"Total: {len(repositorios)} repositório(s)")
    print()


# ============================================================
# INTERPRETAR SELEÇÃO
# ============================================================

def interpretar_selecao(entrada, total):

    entrada = entrada.strip().lower()

    if entrada in ("todos", "tudo", "*"):

        return list(range(1, total + 1))

    numeros = set()

    partes = entrada.split(",")

    for parte in partes:

        parte = parte.strip()

        if not parte:
            continue

        # Intervalo: 5-10
        if "-" in parte:

            extremos = parte.split("-")

            if len(extremos) != 2:
                raise ValueError(
                    f"Intervalo inválido: {parte}"
                )

            inicio = int(extremos[0])
            fim = int(extremos[1])

            if inicio > fim:
                inicio, fim = fim, inicio

            for numero in range(inicio, fim + 1):

                if numero < 1 or numero > total:
                    raise ValueError(
                        f"Número fora do intervalo: {numero}"
                    )

                numeros.add(numero)

        else:

            numero = int(parte)

            if numero < 1 or numero > total:
                raise ValueError(
                    f"Número fora do intervalo: {numero}"
                )

            numeros.add(numero)

    return sorted(numeros)


# ============================================================
# CONFIRMAR SELEÇÃO
# ============================================================

def mostrar_selecionados(repositorios, indices):

    print()
    print("=" * 70)
    print("REPOSITÓRIOS SELECIONADOS")
    print("=" * 70)

    for indice in indices:

        repo = repositorios[indice - 1]

        print(
            f"{indice:4d}. "
            f"{repo['full_name']}"
        )

    print("=" * 70)
    print(
        f"Total selecionado: {len(indices)}"
    )
    print()


# ============================================================
# VERIFICAR REPOSITÓRIO
# ============================================================

def verificar_repositorio(full_name):

    url = f"{API_URL}/repos/{full_name}"

    try:

        response = requests.get(
            url,
            headers=HEADERS,
            timeout=30,
        )

    except requests.RequestException as error:

        print(
            f"  [ERRO DE CONEXÃO] "
            f"{full_name}: {error}"
        )

        return False

    if response.status_code == 200:
        return True

    if response.status_code == 404:

        print(
            f"  [NÃO ENCONTRADO] "
            f"{full_name}"
        )

        return False

    print(
        f"  [ERRO {response.status_code}] "
        f"{full_name}"
    )

    return False


# ============================================================
# EXCLUIR REPOSITÓRIO
# ============================================================

def excluir_repositorio(full_name):

    url = f"{API_URL}/repos/{full_name}"

    try:

        response = requests.delete(
            url,
            headers=HEADERS,
            timeout=30,
        )

    except requests.RequestException as error:

        print(
            f"  [ERRO DE CONEXÃO] "
            f"{full_name}: {error}"
        )

        return False

    if response.status_code == 204:

        print(
            f"  [EXCLUÍDO] "
            f"{full_name}"
        )

        return True

    if response.status_code == 403:

        print(
            f"  [SEM PERMISSÃO] "
            f"{full_name}"
        )

        return False

    if response.status_code == 404:

        print(
            f"  [NÃO ENCONTRADO] "
            f"{full_name}"
        )

        return False

    print(
        f"  [ERRO {response.status_code}] "
        f"{full_name}"
    )

    if response.text:
        print(f"  {response.text}")

    return False


# ============================================================
# PROGRAMA PRINCIPAL
# ============================================================

def main():

    limpar_tela()

    print("=" * 70)
    print("             GITHUB REPOSITORY MANAGER")
    print("=" * 70)

    verificar_configuracao()

    # --------------------------------------------------------
    # LOGIN
    # --------------------------------------------------------

    usuario = obter_usuario()

    login = usuario.get("login", "desconhecido")

    print()
    print(f"Usuário autenticado: {login}")

    # --------------------------------------------------------
    # LISTAR
    # --------------------------------------------------------

    repositorios = listar_repositorios()

    if not repositorios:

        print()
        print("Nenhum repositório encontrado.")
        return

    mostrar_repositorios(repositorios)

    # --------------------------------------------------------
    # SELEÇÃO
    # --------------------------------------------------------

    print("FORMATO DE SELEÇÃO")
    print()
    print("Exemplos:")
    print("  1")
    print("  1,3,5")
    print("  1,3,5-10")
    print("  2-8")
    print("  todos")
    print()

    entrada = input(
        "Digite os números dos repositórios: "
    ).strip()

    try:

        indices = interpretar_selecao(
            entrada,
            len(repositorios),
        )

    except ValueError as error:

        print()
        print(f"ERRO: {error}")
        return

    if not indices:

        print()
        print("Nenhum repositório selecionado.")
        return

    # --------------------------------------------------------
    # MOSTRAR SELEÇÃO
    # --------------------------------------------------------

    mostrar_selecionados(
        repositorios,
        indices,
    )

    # --------------------------------------------------------
    # PRIMEIRA CONFIRMAÇÃO
    # --------------------------------------------------------

    confirmacao = input(
        'Digite "CONFIRMAR" para continuar: '
    ).strip()

    if confirmacao != "CONFIRMAR":

        print()
        print("Operação cancelada.")
        return

    # --------------------------------------------------------
    # SEGUNDA CONFIRMAÇÃO
    # --------------------------------------------------------

    print()
    print("⚠️  ATENÇÃO!")
    print()
    print(
        "Os repositórios selecionados serão "
        "excluídos através da API do GitHub."
    )
    print()

    confirmacao_final = input(
        'Digite "EXCLUIR DEFINITIVAMENTE": '
    ).strip()

    if confirmacao_final != "EXCLUIR DEFINITIVAMENTE":

        print()
        print("Operação cancelada.")
        return

    # --------------------------------------------------------
    # VERIFICAÇÃO
    # --------------------------------------------------------

    print()
    print("=" * 70)
    print("VERIFICANDO REPOSITÓRIOS")
    print("=" * 70)
    print()

    validos = []

    for indice in indices:

        repo = repositorios[indice - 1]

        full_name = repo["full_name"]

        print(f"Verificando: {full_name}")

        if verificar_repositorio(full_name):

            validos.append(full_name)

    if not validos:

        print()
        print("Nenhum repositório está disponível para exclusão.")
        return

    # --------------------------------------------------------
    # EXCLUSÃO
    # --------------------------------------------------------

    print()
    print("=" * 70)
    print("INICIANDO EXCLUSÃO")
    print("=" * 70)
    print()

    excluidos = []
    falhas = []

    for full_name in validos:

        print(f"Processando: {full_name}")

        if excluir_repositorio(full_name):

            excluidos.append(full_name)

        else:

            falhas.append(full_name)

        time.sleep(DELAY_SECONDS)

    # --------------------------------------------------------
    # RELATÓRIO
    # --------------------------------------------------------

    print()
    print("=" * 70)
    print("                         RESULTADO")
    print("=" * 70)
    print()

    print(
        f"Selecionados:       {len(indices)}"
    )

    print(
        f"Excluídos:          {len(excluidos)}"
    )

    print(
        f"Falhas:             {len(falhas)}"
    )

    print()

    if excluidos:

        print("REPOSITÓRIOS EXCLUÍDOS:")

        for repo in excluidos:
            print(f"  ✓ {repo}")

        print()

    if falhas:

        print("REPOSITÓRIOS QUE NÃO FORAM EXCLUÍDOS:")

        for repo in falhas:
            print(f"  ✗ {repo}")

        print()

    print("=" * 70)
    print("Operação concluída.")
    print("=" * 70)


# ============================================================
# EXECUTAR
# ============================================================

if __name__ == "__main__":
    main()
