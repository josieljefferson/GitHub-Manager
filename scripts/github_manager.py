#!/usr/bin/env python3

"""
GitHub Repository Manager
=========================

Gerenciador de repositórios para execução no GitHub Actions.

Recursos:
- Lista automaticamente os repositórios da conta autenticada
- Paginação automática
- Seleção por número
- Suporta:
    3
    1,3,5
    1,3,5-10
    todos
- Executa sem input() no GitHub Actions
- Usa SELECAO_REPOSITORIOS
- Usa CONFIRMACAO
- Exige confirmação explícita
- Relatório final
"""

from __future__ import annotations

import os
import sys
import time
import requests


# ============================================================
# CONFIGURAÇÃO
# ============================================================

API_URL = "https://api.github.com"

PER_PAGE = 100

DELAY_SECONDS = 0.5

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")

SELECAO_REPOSITORIOS = os.getenv(
    "SELECAO_REPOSITORIOS",
    ""
).strip()

CONFIRMACAO = os.getenv(
    "CONFIRMACAO",
    ""
).strip()


# ============================================================
# HEADERS
# ============================================================

HEADERS = {
    "Accept": "application/vnd.github+json",
    "Authorization": f"Bearer {GITHUB_TOKEN}",
    "X-GitHub-Api-Version": "2022-11-28",
}


# ============================================================
# ERRO
# ============================================================

def erro(mensagem: str):

    print()
    print("=" * 70)
    print("ERRO")
    print("=" * 70)
    print()
    print(mensagem)
    print()

    sys.exit(1)


# ============================================================
# VALIDAR TOKEN
# ============================================================

def verificar_configuracao():

    if not GITHUB_TOKEN:

        erro(
            "GITHUB_TOKEN não foi encontrado.\n\n"
            "Verifique se o workflow contém:\n\n"
            "GITHUB_TOKEN: ${{ secrets.MY_GITHUB_TOKEN }}"
        )


# ============================================================
# OBTER USUÁRIO
# ============================================================

def obter_usuario():

    url = f"{API_URL}/user"

    try:

        response = requests.get(
            url,
            headers=HEADERS,
            timeout=30,
        )

    except requests.RequestException as exc:

        erro(
            f"Erro de conexão ao autenticar no GitHub:\n{exc}"
        )

    if response.status_code != 200:

        erro(
            "Não foi possível autenticar no GitHub.\n\n"
            f"HTTP: {response.status_code}\n"
            f"Resposta: {response.text}"
        )

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
            f"&affiliation=owner"
            f"&sort=full_name"
            f"&direction=asc"
        )

        try:

            response = requests.get(
                url,
                headers=HEADERS,
                timeout=30,
            )

        except requests.RequestException as exc:

            erro(
                f"Erro ao consultar os repositórios:\n{exc}"
            )

        if response.status_code != 200:

            erro(
                "Erro ao listar repositórios.\n\n"
                f"HTTP: {response.status_code}\n"
                f"Resposta: {response.text}"
            )

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

    for numero, repo in enumerate(
        repositorios,
        start=1
    ):

        nome = repo.get("name", "")

        visibilidade = (
            "PRIVADO"
            if repo.get("private")
            else "PÚBLICO"
        )

        descricao = (
            repo.get("description")
            or ""
        )

        descricao = (
            descricao
            .replace("\n", " ")
            .strip()
        )

        if len(descricao) > 45:

            descricao = (
                descricao[:42]
                + "..."
            )

        print(
            f"{numero:4d}. "
            f"{nome:<35} "
            f"{visibilidade:<8} "
            f"{descricao}"
        )

    print("=" * 90)
    print(
        f"Total: {len(repositorios)} "
        "repositório(s)"
    )
    print()


# ============================================================
# INTERPRETAR SELEÇÃO
# ============================================================

def interpretar_selecao(
    entrada: str,
    total: int,
):

    entrada = (
        entrada
        .strip()
        .lower()
    )

    if not entrada:

        raise ValueError(
            "Nenhuma seleção foi informada."
        )

    if entrada in (
        "todos",
        "tudo",
        "*",
    ):

        return list(
            range(
                1,
                total + 1
            )
        )

    numeros = set()

    partes = entrada.split(",")

    for parte in partes:

        parte = parte.strip()

        if not parte:
            continue

        # ----------------------------------------------------
        # INTERVALO
        # ----------------------------------------------------

        if "-" in parte:

            extremos = parte.split("-")

            if len(extremos) != 2:

                raise ValueError(
                    f"Intervalo inválido: {parte}"
                )

            try:

                inicio = int(
                    extremos[0].strip()
                )

                fim = int(
                    extremos[1].strip()
                )

            except ValueError:

                raise ValueError(
                    f"Intervalo inválido: {parte}"
                )

            if inicio > fim:

                inicio, fim = (
                    fim,
                    inicio,
                )

            for numero in range(
                inicio,
                fim + 1
            ):

                if (
                    numero < 1
                    or numero > total
                ):

                    raise ValueError(
                        f"Número fora do intervalo: "
                        f"{numero}"
                    )

                numeros.add(numero)

        # ----------------------------------------------------
        # NÚMERO INDIVIDUAL
        # ----------------------------------------------------

        else:

            try:

                numero = int(parte)

            except ValueError:

                raise ValueError(
                    f"Valor inválido: {parte}"
                )

            if (
                numero < 1
                or numero > total
            ):

                raise ValueError(
                    f"Número fora do intervalo: "
                    f"{numero}"
                )

            numeros.add(numero)

    if not numeros:

        raise ValueError(
            "Nenhum repositório foi selecionado."
        )

    return sorted(numeros)


# ============================================================
# MOSTRAR SELECIONADOS
# ============================================================

def mostrar_selecionados(
    repositorios,
    indices,
):

    print()
    print("=" * 70)
    print("REPOSITÓRIOS SELECIONADOS")
    print("=" * 70)

    for indice in indices:

        repo = repositorios[
            indice - 1
        ]

        print(
            f"{indice:4d}. "
            f"{repo['full_name']}"
        )

    print("=" * 70)
    print(
        f"Total selecionado: "
        f"{len(indices)}"
    )
    print()


# ============================================================
# VERIFICAR REPOSITÓRIO
# ============================================================

def verificar_repositorio(
    full_name: str
):

    url = (
        f"{API_URL}/repos/"
        f"{full_name}"
    )

    try:

        response = requests.get(
            url,
            headers=HEADERS,
            timeout=30,
        )

    except requests.RequestException as exc:

        print(
            f"  [ERRO DE CONEXÃO] "
            f"{full_name}: {exc}"
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

def excluir_repositorio(
    full_name: str
):

    url = (
        f"{API_URL}/repos/"
        f"{full_name}"
    )

    try:

        response = requests.delete(
            url,
            headers=HEADERS,
            timeout=30,
        )

    except requests.RequestException as exc:

        print(
            f"  [ERRO DE CONEXÃO] "
            f"{full_name}: {exc}"
        )

        return False

    # GitHub retorna 204 após exclusão
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

        print(
            f"  Resposta: "
            f"{response.text}"
        )

    return False


# ============================================================
# MAIN
# ============================================================

def main():

    print()
    print("=" * 70)
    print("             GITHUB REPOSITORY MANAGER")
    print("=" * 70)

    verificar_configuracao()

    # --------------------------------------------------------
    # AUTENTICAÇÃO
    # --------------------------------------------------------

    usuario = obter_usuario()

    login = usuario.get(
        "login",
        "desconhecido",
    )

    print()
    print(
        f"Usuário autenticado: {login}"
    )

    # --------------------------------------------------------
    # LISTAR
    # --------------------------------------------------------

    repositorios = listar_repositorios()

    if not repositorios:

        erro(
            "Nenhum repositório encontrado."
        )

    mostrar_repositorios(
        repositorios
    )

    # --------------------------------------------------------
    # SELEÇÃO PELO GITHUB ACTIONS
    # --------------------------------------------------------

    entrada = (
        SELECAO_REPOSITORIOS
    )

    print(
        "Seleção recebida pelo workflow:"
    )

    print(
        f"  {entrada}"
    )

    try:

        indices = interpretar_selecao(
            entrada,
            len(repositorios),
        )

    except ValueError as exc:

        erro(str(exc))

    # --------------------------------------------------------
    # CONFIRMAÇÃO
    # --------------------------------------------------------

    if CONFIRMACAO != "EXCLUIR":

        erro(
            "Confirmação inválida.\n\n"
            "Para executar a exclusão, "
            "o campo CONFIRMACAO deve ser:\n\n"
            "EXCLUIR"
        )

    mostrar_selecionados(
        repositorios,
        indices,
    )

    print(
        "Confirmação recebida:"
    )

    print(
        "  EXCLUIR"
    )

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

        repo = repositorios[
            indice - 1
        ]

        full_name = repo[
            "full_name"
        ]

        print(
            f"Verificando: "
            f"{full_name}"
        )

        if verificar_repositorio(
            full_name
        ):

            validos.append(
                full_name
            )

    if not validos:

        erro(
            "Nenhum repositório válido "
            "está disponível para exclusão."
        )

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

        print(
            f"Processando: "
            f"{full_name}"
        )

        if excluir_repositorio(
            full_name
        ):

            excluidos.append(
                full_name
            )

        else:

            falhas.append(
                full_name
            )

        time.sleep(
            DELAY_SECONDS
        )

    # --------------------------------------------------------
    # RELATÓRIO
    # --------------------------------------------------------

    print()
    print("=" * 70)
    print("                     RESULTADO")
    print("=" * 70)
    print()

    print(
        f"Selecionados: {len(indices)}"
    )

    print(
        f"Excluídos:    {len(excluidos)}"
    )

    print(
        f"Falhas:       {len(falhas)}"
    )

    print()

    if excluidos:

        print(
            "REPOSITÓRIOS EXCLUÍDOS:"
        )

        for repo in excluidos:

            print(
                f"  ✓ {repo}"
            )

        print()

    if falhas:

        print(
            "REPOSITÓRIOS COM FALHA:"
        )

        for repo in falhas:

            print(
                f"  ✗ {repo}"
            )

        print()

    print("=" * 70)
    print("Operação concluída.")
    print("=" * 70)


# ============================================================
# EXECUTAR
# ============================================================

if __name__ == "__main__":

    main()
