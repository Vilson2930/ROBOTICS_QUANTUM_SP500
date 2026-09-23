"""
ROBOTICS_QUANTUM_SP500
======================

Módulo responsável pelo universo atual do S&P 500.

FUNÇÃO
------
1. Buscar a composição atual do S&P 500.
2. Normalizar os tickers.
3. Disponibilizar o S&P 500 completo ao pipeline principal.
4. Permitir o cruzamento com o universo temático congelado.

IMPORTANTE
----------
Este módulo NÃO seleciona empresas por fundamentos.

Ele apenas define o universo elegível antes da execução
dos motores fundamentalistas.
"""

from __future__ import annotations

from io import StringIO
from pathlib import Path
from typing import Optional

import pandas as pd
import requests

from config.settings import (
    SP500_SOURCE_URL,
    CURRENT_UNIVERSE_FILE,
    REQUIRE_SP500_MEMBERSHIP,
)

from config.thematic_universe import (
    THEMATIC_UNIVERSE,
    normalize_ticker,
    participates_in_robotics,
    participates_in_quantum,
)


# =============================================================================
# CONFIGURAÇÃO
# =============================================================================

REQUEST_TIMEOUT = 30

REQUEST_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 "
        "(Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 "
        "(KHTML, like Gecko) "
        "Chrome/120.0 Safari/537.36"
    )
}


# =============================================================================
# COLUNAS PADRÃO
# =============================================================================

STANDARD_COLUMNS = [
    "ticker",
    "company",
    "gics_sector",
    "gics_sub_industry",
    "headquarters",
    "date_added",
    "cik",
    "founded",
]


# =============================================================================
# NORMALIZAÇÃO
# =============================================================================

def _normalize_columns(
    df: pd.DataFrame,
) -> pd.DataFrame:
    """
    Converte as colunas da tabela do S&P 500
    para o padrão interno do projeto.
    """

    column_map = {
        "Symbol": "ticker",
        "Security": "company",
        "GICS Sector": "gics_sector",
        "GICS Sub-Industry": "gics_sub_industry",
        "Headquarters Location": "headquarters",
        "Date added": "date_added",
        "CIK": "cik",
        "Founded": "founded",
    }

    missing = [
        column
        for column in column_map
        if column not in df.columns
    ]

    if missing:
        raise ValueError(
            "Colunas esperadas não encontradas "
            f"na fonte do S&P 500: {missing}"
        )

    result = (
        df[list(column_map.keys())]
        .rename(columns=column_map)
        .copy()
    )

    result["ticker"] = (
        result["ticker"]
        .astype(str)
        .map(normalize_ticker)
    )

    result["company"] = (
        result["company"]
        .astype(str)
        .str.strip()
    )

    result["gics_sector"] = (
        result["gics_sector"]
        .astype(str)
        .str.strip()
    )

    result["gics_sub_industry"] = (
        result["gics_sub_industry"]
        .astype(str)
        .str.strip()
    )

    result["headquarters"] = (
        result["headquarters"]
        .astype(str)
        .str.strip()
    )

    result["date_added"] = pd.to_datetime(
        result["date_added"],
        errors="coerce",
    )

    result["cik"] = pd.to_numeric(
        result["cik"],
        errors="coerce",
    ).astype("Int64")

    result = (
        result
        .drop_duplicates(
            subset=["ticker"],
            keep="first",
        )
        .sort_values("ticker")
        .reset_index(drop=True)
    )

    return result


# =============================================================================
# DOWNLOAD DO S&P 500
# =============================================================================

def download_sp500() -> pd.DataFrame:
    """
    Baixa a composição atual do S&P 500.

    A fonte é definida em config/settings.py.

    Returns
    -------
    pd.DataFrame
        Universo atual normalizado.
    """

    response = requests.get(
        SP500_SOURCE_URL,
        headers=REQUEST_HEADERS,
        timeout=REQUEST_TIMEOUT,
    )

    response.raise_for_status()

    tables = pd.read_html(
        StringIO(response.text)
    )

    if not tables:
        raise RuntimeError(
            "Nenhuma tabela encontrada "
            "na fonte do S&P 500."
        )

    target_table: Optional[pd.DataFrame] = None

    for table in tables:

        required = {
            "Symbol",
            "Security",
            "GICS Sector",
            "GICS Sub-Industry",
            "CIK",
        }

        if required.issubset(
            set(table.columns)
        ):
            target_table = table
            break

    if target_table is None:
        raise RuntimeError(
            "Tabela oficial de constituintes "
            "do S&P 500 não identificada."
        )

    result = _normalize_columns(
        target_table
    )

    if len(result) < 490:
        raise RuntimeError(
            "Quantidade inesperadamente baixa "
            f"de empresas no S&P 500: {len(result)}"
        )

    if len(result) > 510:
        raise RuntimeError(
            "Quantidade inesperadamente alta "
            f"de empresas no S&P 500: {len(result)}"
        )

    return result


# =============================================================================
# INTERFACE PRINCIPAL PARA O MAIN.PY
# =============================================================================

def get_sp500_universe(
    save: bool = True,
) -> pd.DataFrame:
    """
    Retorna o universo COMPLETO e atual do S&P 500.

    Esta é a interface utilizada pelo main.py.

    IMPORTANTE
    ----------
    Esta função NÃO aplica classificação temática.

    A classificação Robotics / Quantum ocorre posteriormente
    no ThematicClassifier, preservando a arquitetura:

        S&P 500
            ↓
        ThematicClassifier
            ↓
        FundamentalData
            ↓
        FundamentalSelection
    """

    sp500 = download_sp500()

    validate_sp500(
        sp500
    )

    if save:
        save_current_universe(
            sp500
        )

    return sp500


# =============================================================================
# UNIVERSO TEMÁTICO ELEGÍVEL
# =============================================================================

def build_thematic_sp500_universe(
    sp500: pd.DataFrame,
) -> pd.DataFrame:
    """
    Cruza o S&P 500 atual com o universo temático.

    Uma empresa só será elegível se estiver:
    1. no universo temático;
    2. no S&P 500 atual.
    """

    if "ticker" not in sp500.columns:
        raise ValueError(
            "DataFrame do S&P 500 sem coluna ticker."
        )

    current_tickers = set(
        sp500["ticker"]
        .dropna()
        .astype(str)
        .map(normalize_ticker)
    )

    rows = []

    for ticker, thematic in (
        THEMATIC_UNIVERSE.items()
    ):

        ticker = normalize_ticker(
            ticker
        )

        in_sp500 = (
            ticker in current_tickers
        )

        if (
            REQUIRE_SP500_MEMBERSHIP
            and not in_sp500
        ):
            continue

        sp_row = sp500.loc[
            sp500["ticker"] == ticker
        ]

        if sp_row.empty:
            continue

        sp_row = sp_row.iloc[0]

        rows.append(
            {
                "ticker":
                    ticker,

                "company":
                    sp_row["company"],

                "thematic_company":
                    thematic["company"],

                "theme":
                    thematic["theme"],

                "exposure":
                    thematic["exposure"],

                "robotics":
                    participates_in_robotics(
                        ticker
                    ),

                "quantum":
                    participates_in_quantum(
                        ticker
                    ),

                "in_sp500":
                    in_sp500,

                "gics_sector":
                    sp_row["gics_sector"],

                "gics_sub_industry":
                    sp_row[
                        "gics_sub_industry"
                    ],

                "headquarters":
                    sp_row["headquarters"],

                "date_added":
                    sp_row["date_added"],

                "cik":
                    sp_row["cik"],

                "founded":
                    sp_row["founded"],
            }
        )

    result = pd.DataFrame(
        rows
    )

    if result.empty:
        raise RuntimeError(
            "Nenhuma empresa temática "
            "foi encontrada no S&P 500."
        )

    result = (
        result
        .sort_values(
            [
                "theme",
                "ticker",
            ]
        )
        .reset_index(drop=True)
    )

    return result


# =============================================================================
# AUDITORIA DE EMPRESAS FORA DO ÍNDICE
# =============================================================================

def find_thematic_companies_outside_sp500(
    sp500: pd.DataFrame,
) -> pd.DataFrame:
    """
    Identifica empresas do universo temático congelado
    que não pertencem mais ao S&P 500.
    """

    current_tickers = set(
        sp500["ticker"]
        .dropna()
        .astype(str)
        .map(normalize_ticker)
    )

    rows = []

    for ticker, config in (
        THEMATIC_UNIVERSE.items()
    ):

        normalized = normalize_ticker(
            ticker
        )

        if normalized not in current_tickers:

            rows.append(
                {
                    "ticker":
                        normalized,

                    "company":
                        config["company"],

                    "theme":
                        config["theme"],

                    "exposure":
                        config["exposure"],

                    "reason":
                        "NOT_CURRENTLY_IN_SP500",
                }
            )

    return pd.DataFrame(
        rows
    )


# =============================================================================
# VALIDAÇÕES
# =============================================================================

def validate_sp500(
    sp500: pd.DataFrame,
) -> bool:
    """
    Executa verificações básicas de integridade.
    """

    if sp500.empty:
        raise AssertionError(
            "S&P 500 vazio."
        )

    required_columns = {
        "ticker",
        "company",
        "gics_sector",
        "gics_sub_industry",
        "cik",
    }

    missing = (
        required_columns
        - set(sp500.columns)
    )

    if missing:
        raise AssertionError(
            "Colunas obrigatórias ausentes: "
            f"{sorted(missing)}"
        )

    if sp500["ticker"].duplicated().any():

        duplicates = (
            sp500.loc[
                sp500["ticker"].duplicated(
                    keep=False
                ),
                "ticker",
            ]
            .tolist()
        )

        raise AssertionError(
            "Tickers duplicados no S&P 500: "
            f"{duplicates}"
        )

    if len(sp500) < 490:
        raise AssertionError(
            "Universo S&P 500 "
            "anormalmente pequeno."
        )

    if len(sp500) > 510:
        raise AssertionError(
            "Universo S&P 500 "
            "anormalmente grande."
        )

    return True


def validate_thematic_universe(
    thematic: pd.DataFrame,
) -> bool:
    """
    Valida o resultado do cruzamento temático.
    """

    if thematic.empty:
        raise AssertionError(
            "Universo temático elegível vazio."
        )

    if (
        REQUIRE_SP500_MEMBERSHIP
        and not thematic["in_sp500"].all()
    ):
        raise AssertionError(
            "Empresa fora do S&P 500 "
            "entrou no universo elegível."
        )

    allowed = {
        "ROBOTICS",
        "QUANTUM",
        "BOTH",
    }

    invalid = set(
        thematic["theme"]
    ) - allowed

    if invalid:
        raise AssertionError(
            "Temas inválidos encontrados: "
            f"{sorted(invalid)}"
        )

    return True


# =============================================================================
# SALVAR RESULTADOS
# =============================================================================

def save_current_universe(
    sp500: pd.DataFrame,
) -> Path:
    """
    Salva o snapshot atual do S&P 500.
    """

    output = Path(
        CURRENT_UNIVERSE_FILE
    )

    output.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    sp500.to_csv(
        output,
        index=False,
    )

    return output


# =============================================================================
# INTERFACE ALTERNATIVA
# =============================================================================

def get_current_universe(
    save: bool = True,
) -> pd.DataFrame:
    """
    Retorna apenas as empresas temáticas
    atualmente elegíveis no S&P 500.

    Mantida por compatibilidade.

    Para o pipeline principal do robô deve ser utilizada:
        get_sp500_universe()
    """

    sp500 = get_sp500_universe(
        save=save
    )

    thematic = (
        build_thematic_sp500_universe(
            sp500
        )
    )

    validate_thematic_universe(
        thematic
    )

    return thematic


# =============================================================================
# EXECUÇÃO MANUAL
# =============================================================================

if __name__ == "__main__":

    print(
        "=" * 90
    )

    print(
        "ROBOTICS_QUANTUM_SP500 — "
        "S&P 500 UNIVERSE"
    )

    print(
        "=" * 90
    )

    sp500 = get_sp500_universe(
        save=True
    )

    thematic = (
        build_thematic_sp500_universe(
            sp500
        )
    )

    validate_thematic_universe(
        thematic
    )

    outside = (
        find_thematic_companies_outside_sp500(
            sp500
        )
    )

    print(
        f"\nS&P 500 atual: "
        f"{len(sp500)} empresas"
    )

    print(
        f"Empresas temáticas elegíveis: "
        f"{len(thematic)}"
    )

    print(
        f"Robotics: "
        f"{int(thematic['robotics'].sum())}"
    )

    print(
        f"Quantum: "
        f"{int(thematic['quantum'].sum())}"
    )

    print(
        "\nUniverso elegível:"
    )

    print(
        thematic[
            [
                "ticker",
                "company",
                "theme",
                "exposure",
                "gics_sector",
            ]
        ].to_string(
            index=False
        )
    )

    if outside.empty:

        print(
            "\nTodas as empresas temáticas "
            "permanecem no S&P 500."
        )

    else:

        print(
            "\nEmpresas temáticas atualmente "
            "fora do S&P 500:"
        )

        print(
            outside.to_string(
                index=False
            )
        )

    print(
        "\nMódulo concluído com sucesso."
    )
