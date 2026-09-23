"""
ROBOTICS_QUANTUM_SP500
======================

Classificador temático operacional.

RESPONSABILIDADE
----------------
Receber o universo temático que já passou pelo filtro do S&P 500
e produzir os universos independentes:

- ROBOTICS
- QUANTUM

Empresas classificadas como BOTH participam dos dois motores.

IMPORTANTE
----------
Este módulo NÃO decide se uma empresa é boa ou ruim.

Ele NÃO calcula fundamentos.
Ele NÃO calcula timing.
Ele NÃO altera o universo S&P 500.

A função é somente organizar corretamente as empresas elegíveis
para os dois motores do robô.

O setor GICS REAL é preservado para uso posterior pelo
AI Infrastructure Scanner.
"""

from __future__ import annotations

from typing import Dict

import pandas as pd

from config.thematic_universe import (
    ALLOWED_THEMES,
)


# =============================================================================
# COLUNAS OBRIGATÓRIAS
# =============================================================================

REQUIRED_COLUMNS = {
    "ticker",
    "company",
    "theme",
    "exposure",
    "robotics",
    "quantum",
    "in_sp500",
    "gics_sector",
    "gics_sub_industry",
    "cik",
}


# =============================================================================
# VALIDAÇÃO DA ENTRADA
# =============================================================================

def validate_input(
    universe: pd.DataFrame,
) -> bool:
    """
    Valida o universo recebido do módulo
    data/sp500_universe.py.
    """

    if not isinstance(
        universe,
        pd.DataFrame,
    ):
        raise TypeError(
            "O universo deve ser um pandas DataFrame."
        )

    if universe.empty:
        raise ValueError(
            "Universo temático vazio."
        )

    missing = (
        REQUIRED_COLUMNS
        - set(universe.columns)
    )

    if missing:
        raise ValueError(
            "Colunas obrigatórias ausentes: "
            f"{sorted(missing)}"
        )

    if universe["ticker"].isna().any():
        raise ValueError(
            "Ticker ausente no universo."
        )

    if universe["ticker"].duplicated().any():
        duplicates = (
            universe.loc[
                universe["ticker"].duplicated(
                    keep=False
                ),
                "ticker",
            ]
            .astype(str)
            .tolist()
        )

        raise ValueError(
            "Tickers duplicados no universo: "
            f"{duplicates}"
        )

    invalid_themes = (
        set(
            universe["theme"]
            .dropna()
            .astype(str)
        )
        - ALLOWED_THEMES
    )

    if invalid_themes:
        raise ValueError(
            "Temas inválidos encontrados: "
            f"{sorted(invalid_themes)}"
        )

    if not universe["in_sp500"].fillna(False).all():
        raise ValueError(
            "Empresa fora do S&P 500 entrou "
            "no classificador temático."
        )

    return True


# =============================================================================
# NORMALIZAÇÃO
# =============================================================================

def normalize_universe(
    universe: pd.DataFrame,
) -> pd.DataFrame:
    """
    Normaliza tipos e valores usados pelo classificador.
    """

    df = universe.copy()

    df["ticker"] = (
        df["ticker"]
        .astype(str)
        .str.strip()
        .str.upper()
    )

    df["theme"] = (
        df["theme"]
        .astype(str)
        .str.strip()
        .str.upper()
    )

    df["exposure"] = (
        df["exposure"]
        .astype(str)
        .str.strip()
        .str.upper()
    )

    df["gics_sector"] = (
        df["gics_sector"]
        .astype(str)
        .str.strip()
    )

    df["gics_sub_industry"] = (
        df["gics_sub_industry"]
        .astype(str)
        .str.strip()
    )

    df["robotics"] = (
        df["robotics"]
        .astype(bool)
    )

    df["quantum"] = (
        df["quantum"]
        .astype(bool)
    )

    df["in_sp500"] = (
        df["in_sp500"]
        .astype(bool)
    )

    return df


# =============================================================================
# ROBOTICS
# =============================================================================

def build_robotics_universe(
    universe: pd.DataFrame,
) -> pd.DataFrame:
    """
    Cria universo Robotics.

    Inclui:
    - ROBOTICS
    - BOTH
    """

    validate_input(
        universe
    )

    df = normalize_universe(
        universe
    )

    robotics = (
        df.loc[
            df["robotics"]
        ]
        .copy()
    )

    if robotics.empty:
        raise RuntimeError(
            "Nenhuma empresa elegível "
            "no universo Robotics."
        )

    invalid = robotics.loc[
        ~robotics["theme"].isin(
            [
                "ROBOTICS",
                "BOTH",
            ]
        )
    ]

    if not invalid.empty:
        raise AssertionError(
            "Empresa incompatível entrou "
            "no motor Robotics."
        )

    robotics["ranking_theme"] = (
        "ROBOTICS"
    )

    robotics = (
        robotics
        .sort_values(
            [
                "exposure",
                "ticker",
            ]
        )
        .reset_index(drop=True)
    )

    return robotics


# =============================================================================
# QUANTUM
# =============================================================================

def build_quantum_universe(
    universe: pd.DataFrame,
) -> pd.DataFrame:
    """
    Cria universo Quantum.

    Inclui:
    - QUANTUM
    - BOTH
    """

    validate_input(
        universe
    )

    df = normalize_universe(
        universe
    )

    quantum = (
        df.loc[
            df["quantum"]
        ]
        .copy()
    )

    if quantum.empty:
        raise RuntimeError(
            "Nenhuma empresa elegível "
            "no universo Quantum."
        )

    invalid = quantum.loc[
        ~quantum["theme"].isin(
            [
                "QUANTUM",
                "BOTH",
            ]
        )
    ]

    if not invalid.empty:
        raise AssertionError(
            "Empresa incompatível entrou "
            "no motor Quantum."
        )

    quantum["ranking_theme"] = (
        "QUANTUM"
    )

    quantum = (
        quantum
        .sort_values(
            [
                "exposure",
                "ticker",
            ]
        )
        .reset_index(drop=True)
    )

    return quantum


# =============================================================================
# CLASSIFICADOR COMPLETO
# =============================================================================

def classify_themes(
    universe: pd.DataFrame,
) -> Dict[str, pd.DataFrame]:
    """
    Executa a separação oficial dos dois motores.

    Returns
    -------
    dict

    {
        "ROBOTICS": DataFrame,
        "QUANTUM": DataFrame
    }
    """

    validate_input(
        universe
    )

    robotics = (
        build_robotics_universe(
            universe
        )
    )

    quantum = (
        build_quantum_universe(
            universe
        )
    )

    validate_classification(
        universe=universe,
        robotics=robotics,
        quantum=quantum,
    )

    return {
        "ROBOTICS": robotics,
        "QUANTUM": quantum,
    }


# =============================================================================
# AUDITORIA
# =============================================================================

def validate_classification(
    universe: pd.DataFrame,
    robotics: pd.DataFrame,
    quantum: pd.DataFrame,
) -> bool:
    """
    Audita se a separação temática foi executada
    sem perda ou inclusão indevida.
    """

    source = normalize_universe(
        universe
    )

    robotics_expected = set(
        source.loc[
            source["robotics"],
            "ticker",
        ]
    )

    quantum_expected = set(
        source.loc[
            source["quantum"],
            "ticker",
        ]
    )

    robotics_actual = set(
        robotics["ticker"]
    )

    quantum_actual = set(
        quantum["ticker"]
    )

    if (
        robotics_expected
        != robotics_actual
    ):
        raise AssertionError(
            "Universo Robotics divergiu "
            "da classificação temática."
        )

    if (
        quantum_expected
        != quantum_actual
    ):
        raise AssertionError(
            "Universo Quantum divergiu "
            "da classificação temática."
        )

    both_expected = set(
        source.loc[
            source["theme"] == "BOTH",
            "ticker",
        ]
    )

    both_robotics = (
        both_expected
        & robotics_actual
    )

    both_quantum = (
        both_expected
        & quantum_actual
    )

    if (
        both_robotics
        != both_expected
    ):
        raise AssertionError(
            "Empresa BOTH ausente "
            "do universo Robotics."
        )

    if (
        both_quantum
        != both_expected
    ):
        raise AssertionError(
            "Empresa BOTH ausente "
            "do universo Quantum."
        )

    # -------------------------------------------------------------------------
    # GICS deve permanecer disponível.
    # -------------------------------------------------------------------------

    if robotics[
        "gics_sector"
    ].isna().any():
        raise AssertionError(
            "Setor GICS ausente no universo Robotics."
        )

    if quantum[
        "gics_sector"
    ].isna().any():
        raise AssertionError(
            "Setor GICS ausente no universo Quantum."
        )

    return True


# =============================================================================
# RESUMO
# =============================================================================

def classification_summary(
    classified: Dict[str, pd.DataFrame],
) -> pd.DataFrame:
    """
    Gera resumo dos universos.
    """

    rows = []

    for theme in (
        "ROBOTICS",
        "QUANTUM",
    ):

        df = classified[
            theme
        ]

        rows.append(
            {
                "ranking_theme":
                    theme,

                "companies":
                    len(df),

                "direct":
                    int(
                        (
                            df["exposure"]
                            == "DIRECT"
                        ).sum()
                    ),

                "strategic":
                    int(
                        (
                            df["exposure"]
                            == "STRATEGIC"
                        ).sum()
                    ),

                "enabler":
                    int(
                        (
                            df["exposure"]
                            == "ENABLER"
                        ).sum()
                    ),

                "both":
                    int(
                        (
                            df["theme"]
                            == "BOTH"
                        ).sum()
                    ),
            }
        )

    return pd.DataFrame(
        rows
    )


# =============================================================================
# EXIBIÇÃO
# =============================================================================

def print_classification(
    classified: Dict[str, pd.DataFrame],
) -> None:
    """
    Exibe os dois universos classificados.
    """

    print(
        "=" * 100
    )

    print(
        "ROBOTICS_QUANTUM_SP500 — "
        "CLASSIFICAÇÃO TEMÁTICA"
    )

    print(
        "=" * 100
    )

    for theme in (
        "ROBOTICS",
        "QUANTUM",
    ):

        df = classified[
            theme
        ]

        print(
            f"\n{theme}"
        )

        print(
            "-" * 100
        )

        print(
            df[
                [
                    "ticker",
                    "company",
                    "theme",
                    "exposure",
                    "gics_sector",
                    "gics_sub_industry",
                ]
            ].to_string(
                index=False
            )
        )

    print(
        "\nRESUMO"
    )

    print(
        classification_summary(
            classified
        ).to_string(
            index=False
        )
    )
