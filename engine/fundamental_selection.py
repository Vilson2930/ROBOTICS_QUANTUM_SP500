# ======================================================================================
# ROBOTICS_QUANTUM_SP500
# engine/fundamental_selection.py
# ======================================================================================
#
# RESPONSABILIDADE
# ---------------
# Selecionar as melhores empresas do universo temático:
#
# ROBOTICS
#   -> Financial Strength
#   -> Top 5
#
# QUANTUM
#   -> Growth
#   -> Top 2
#
# METODOLOGIA FUNDAMENTAL
# -----------------------
# Reproduz a metodologia validada no PORTFOLIO ACOES AMERICANO:
#
#   1. métricas fundamentais
#   2. winsorização P5-P95 dentro do universo do tema
#   3. percentis dentro do universo do tema
#   4. média dos componentes válidos
#   5. mínimo de 2 componentes
#   6. ranking fundamental
#   7. Top N
#
# IMPORTANTE
# ----------
# • BOTH participa independentemente de ROBOTICS e QUANTUM.
# • Timing NÃO participa desta seleção.
# • Timing NÃO altera ranking fundamental.
# • Timing NÃO altera propriedade.
# • Timing NÃO gera venda.
# • A proteção de fronteira 5º x 6º do robô original NÃO é utilizada aqui,
#   pois não foi validada no estudo ROBOTICS_QUANTUM_SP500.
#
# ======================================================================================

from __future__ import annotations

import numpy as np
import pandas as pd

from config.fundamental_policy import (
    FACTOR_DEFINITIONS,
    THEME_POLICY,
    validate_frozen_policy,
)


# ======================================================================================
# 1. CONSTANTES
# ======================================================================================

ROBOTICS_THEME = "ROBOTICS"
QUANTUM_THEME = "QUANTUM"
BOTH_THEME = "BOTH"

ROBOTICS_FACTOR = "financial_strength"
QUANTUM_FACTOR = "growth"

ROBOTICS_TOP_N = 5
QUANTUM_TOP_N = 2


# ======================================================================================
# 2. HELPERS
# ======================================================================================

def normalize_ticker(
    ticker: str,
) -> str:

    return (
        str(ticker)
        .upper()
        .strip()
        .replace(".", "-")
    )


def winsorize_series(
    series: pd.Series,
) -> pd.Series:
    """
    Winsorização P5-P95.

    Reprodução da metodologia do robô fundamental original.

    Se houver menos de 10 valores válidos, não aplica winsorização.
    """

    values = pd.to_numeric(
        series,
        errors="coerce",
    )

    valid = values.dropna()

    if len(valid) < 10:
        return values

    lower = valid.quantile(0.05)
    upper = valid.quantile(0.95)

    return values.clip(
        lower=lower,
        upper=upper,
    )


def percentile_score(
    series: pd.Series,
    lower_is_better: bool = False,
) -> pd.Series:
    """
    Score maior = empresa melhor.

    Reprodução exata da lógica do selection.py oficial:

        values.rank(
            pct=True,
            ascending=not lower_is_better,
            method="average",
        )

    Portanto:

    higher is better:
        ascending=True

    lower is better:
        ascending=False
    """

    values = pd.to_numeric(
        series,
        errors="coerce",
    )

    return values.rank(
        pct=True,
        ascending=not lower_is_better,
        method="average",
    )


# ======================================================================================
# 3. NORMALIZAÇÃO DO SNAPSHOT
# ======================================================================================

def prepare_fundamental_snapshot(
    fundamentals: pd.DataFrame,
) -> pd.DataFrame:

    if fundamentals is None:
        raise ValueError(
            "Snapshot fundamental não informado."
        )

    if fundamentals.empty:
        raise ValueError(
            "Snapshot fundamental vazio."
        )

    df = fundamentals.copy()

    if "ticker" not in df.columns:
        raise ValueError(
            "Snapshot fundamental precisa conter 'ticker'."
        )

    df["ticker"] = (
        df["ticker"]
        .map(
            normalize_ticker
        )
    )

    required_metrics = [
        "cash_assets",
        "debt_assets",
        "debt_equity",
        "revenue_growth",
        "eps_growth",
        "operating_cash_flow_growth",
    ]

    for column in required_metrics:

        if column not in df.columns:
            df[column] = np.nan

        df[column] = (
            pd.to_numeric(
                df[column],
                errors="coerce",
            )
            .replace(
                [
                    np.inf,
                    -np.inf,
                ],
                np.nan,
            )
        )

    return (
        df
        .drop_duplicates(
            subset=[
                "ticker"
            ]
        )
        .reset_index(
            drop=True
        )
    )


# ======================================================================================
# 4. UNIVERSO DE CADA TEMA
# ======================================================================================

def _get_theme_column(
    df: pd.DataFrame,
) -> str:

    candidates = [
        "theme",
        "thematic_theme",
        "classification",
    ]

    for column in candidates:

        if column in df.columns:
            return column

    raise ValueError(
        "Snapshot fundamental não contém coluna temática. "
        "Esperado: 'theme'."
    )


def build_theme_universe(
    fundamentals: pd.DataFrame,
    ranking_theme: str,
) -> pd.DataFrame:
    """
    Constrói o universo independente de cada ranking.

    ROBOTICS:
        ROBOTICS + BOTH

    QUANTUM:
        QUANTUM + BOTH
    """

    df = prepare_fundamental_snapshot(
        fundamentals
    )

    theme_column = _get_theme_column(
        df
    )

    themes = (
        df[theme_column]
        .astype(str)
        .str.upper()
        .str.strip()
    )

    if ranking_theme == ROBOTICS_THEME:

        mask = themes.isin(
            [
                ROBOTICS_THEME,
                BOTH_THEME,
            ]
        )

    elif ranking_theme == QUANTUM_THEME:

        mask = themes.isin(
            [
                QUANTUM_THEME,
                BOTH_THEME,
            ]
        )

    else:

        raise ValueError(
            f"Tema de ranking desconhecido: "
            f"{ranking_theme}"
        )

    result = df[
        mask
    ].copy()

    result[
        "ranking_theme"
    ] = ranking_theme

    return (
        result
        .drop_duplicates(
            subset=[
                "ticker"
            ]
        )
        .reset_index(
            drop=True
        )
    )


# ======================================================================================
# 5. SCORE GENÉRICO DE FATOR
# ======================================================================================

def calculate_factor_score(
    theme_df: pd.DataFrame,
    factor_name: str,
) -> pd.DataFrame:
    """
    Reprodução da metodologia do selection.py oficial.

    O DataFrame recebido contém somente empresas participantes
    daquele tema.

    Portanto, winsorização e percentis são calculados
    transversalmente dentro do universo temático correspondente.
    """

    if factor_name not in FACTOR_DEFINITIONS:

        raise RuntimeError(
            f"Fator desconhecido: "
            f"{factor_name}"
        )

    df = theme_df.copy()

    definition = (
        FACTOR_DEFINITIONS[
            factor_name
        ]
    )

    higher_metrics = list(
        definition["higher"]
    )

    lower_metrics = list(
        definition["lower"]
    )

    all_metrics = (
        higher_metrics
        +
        lower_metrics
    )

    for metric in all_metrics:

        if metric not in df.columns:
            df[metric] = np.nan

        df[metric] = (
            pd.to_numeric(
                df[metric],
                errors="coerce",
            )
            .replace(
                [
                    np.inf,
                    -np.inf,
                ],
                np.nan,
            )
        )

    # ------------------------------------------------------------------
    # WINSORIZAÇÃO P5-P95
    # ------------------------------------------------------------------

    winsorized = pd.DataFrame(
        index=df.index
    )

    for metric in all_metrics:

        winsorized[
            metric
        ] = winsorize_series(
            df[metric]
        )

    # ------------------------------------------------------------------
    # PERCENTIS
    # ------------------------------------------------------------------

    components = pd.DataFrame(
        index=df.index
    )

    for metric in higher_metrics:

        components[
            metric
        ] = percentile_score(
            winsorized[metric],
            lower_is_better=False,
        )

    for metric in lower_metrics:

        components[
            metric
        ] = percentile_score(
            winsorized[metric],
            lower_is_better=True,
        )

    # ------------------------------------------------------------------
    # COMPONENTES DISPONÍVEIS
    # ------------------------------------------------------------------

    components_column = (
        f"{factor_name}_components"
    )

    score_column = (
        f"{factor_name}_score"
    )

    df[
        components_column
    ] = (
        components
        .notna()
        .sum(
            axis=1
        )
    )

    # ------------------------------------------------------------------
    # SCORE DEFINITIVO
    #
    # Média dos percentis válidos.
    # ------------------------------------------------------------------

    df[
        score_column
    ] = (
        components
        .mean(
            axis=1,
            skipna=True,
        )
    )

    minimum_components = int(
        definition[
            "minimum_components"
        ]
    )

    df.loc[
        df[
            components_column
        ]
        <
        minimum_components,
        score_column,
    ] = np.nan

    return df


# ======================================================================================
# 6. FINANCIAL STRENGTH
# ======================================================================================

def calculate_financial_strength_score(
    theme_df: pd.DataFrame,
) -> pd.DataFrame:

    return calculate_factor_score(
        theme_df=
            theme_df,
        factor_name=
            ROBOTICS_FACTOR,
    )


# ======================================================================================
# 7. GROWTH
# ======================================================================================

def calculate_growth_score(
    theme_df: pd.DataFrame,
) -> pd.DataFrame:

    return calculate_factor_score(
        theme_df=
            theme_df,
        factor_name=
            QUANTUM_FACTOR,
    )


# ======================================================================================
# 8. RANKING ROBOTICS
# ======================================================================================

def rank_robotics(
    fundamentals: pd.DataFrame,
) -> pd.DataFrame:
    """
    ROBOTICS:

        Financial Strength
            cash_assets ↑
            debt_assets ↓
            debt_equity ↓

        Top 5
    """

    robotics = build_theme_universe(
        fundamentals=
            fundamentals,
        ranking_theme=
            ROBOTICS_THEME,
    )

    if robotics.empty:

        raise RuntimeError(
            "Universo ROBOTICS vazio."
        )

    scored = (
        calculate_financial_strength_score(
            robotics
        )
    )

    score_column = (
        "financial_strength_score"
    )

    scored = (
        scored[
            scored[
                score_column
            ].notna()
        ]
        .sort_values(
            [
                score_column,
                "ticker",
            ],
            ascending=[
                False,
                True,
            ],
        )
        .reset_index(
            drop=True
        )
    )

    if len(scored) < ROBOTICS_TOP_N:

        raise RuntimeError(
            "ROBOTICS possui somente "
            f"{len(scored)} empresas elegíveis. "
            f"São necessárias pelo menos "
            f"{ROBOTICS_TOP_N}."
        )

    scored[
        "fundamental_position"
    ] = np.arange(
        1,
        len(scored) + 1,
    )

    scored[
        "fundamental_rank"
    ] = scored[
        "fundamental_position"
    ]

    scored[
        "fundamental_factor"
    ] = ROBOTICS_FACTOR

    scored[
        "fundamental_score"
    ] = scored[
        score_column
    ]

    scored[
        "selected_fundamentally"
    ] = (
        scored[
            "fundamental_position"
        ]
        <=
        ROBOTICS_TOP_N
    )

    return scored


# ======================================================================================
# 9. RANKING QUANTUM
# ======================================================================================

def rank_quantum(
    fundamentals: pd.DataFrame,
) -> pd.DataFrame:
    """
    QUANTUM:

        Growth
            revenue_growth ↑
            eps_growth ↑
            operating_cash_flow_growth ↑

        Top 2
    """

    quantum = build_theme_universe(
        fundamentals=
            fundamentals,
        ranking_theme=
            QUANTUM_THEME,
    )

    if quantum.empty:

        raise RuntimeError(
            "Universo QUANTUM vazio."
        )

    scored = (
        calculate_growth_score(
            quantum
        )
    )

    score_column = (
        "growth_score"
    )

    scored = (
        scored[
            scored[
                score_column
            ].notna()
        ]
        .sort_values(
            [
                score_column,
                "ticker",
            ],
            ascending=[
                False,
                True,
            ],
        )
        .reset_index(
            drop=True
        )
    )

    if len(scored) < QUANTUM_TOP_N:

        raise RuntimeError(
            "QUANTUM possui somente "
            f"{len(scored)} empresas elegíveis. "
            f"São necessárias pelo menos "
            f"{QUANTUM_TOP_N}."
        )

    scored[
        "fundamental_position"
    ] = np.arange(
        1,
        len(scored) + 1,
    )

    scored[
        "fundamental_rank"
    ] = scored[
        "fundamental_position"
    ]

    scored[
        "fundamental_factor"
    ] = QUANTUM_FACTOR

    scored[
        "fundamental_score"
    ] = scored[
        score_column
    ]

    scored[
        "selected_fundamentally"
    ] = (
        scored[
            "fundamental_position"
        ]
        <=
        QUANTUM_TOP_N
    )

    return scored


# ======================================================================================
# 10. SELEÇÃO FUNDAMENTAL FINAL
# ======================================================================================

def select_fundamental_portfolio(
    fundamentals: pd.DataFrame,
) -> pd.DataFrame:

    robotics_ranking = (
        rank_robotics(
            fundamentals
        )
    )

    quantum_ranking = (
        rank_quantum(
            fundamentals
        )
    )

    robotics_selected = (
        robotics_ranking[
            robotics_ranking[
                "selected_fundamentally"
            ]
        ]
        .copy()
    )

    quantum_selected = (
        quantum_ranking[
            quantum_ranking[
                "selected_fundamentally"
            ]
        ]
        .copy()
    )

    final_selection = pd.concat(
        [
            robotics_selected,
            quantum_selected,
        ],
        ignore_index=True,
    )

    return final_selection


# ======================================================================================
# 11. VALIDAÇÃO DA ARQUITETURA CONGELADA
# ======================================================================================

def validate_fundamental_selection(
    selection: pd.DataFrame,
) -> None:

    if selection is None:
        raise RuntimeError(
            "Seleção fundamental inexistente."
        )

    if selection.empty:
        raise RuntimeError(
            "Seleção fundamental vazia."
        )

    required_columns = {
        "ticker",
        "ranking_theme",
        "fundamental_position",
        "fundamental_factor",
        "fundamental_score",
        "selected_fundamentally",
    }

    missing = (
        required_columns
        -
        set(
            selection.columns
        )
    )

    if missing:

        raise RuntimeError(
            "Seleção fundamental sem colunas: "
            f"{sorted(missing)}"
        )

    robotics = selection[
        selection[
            "ranking_theme"
        ]
        ==
        ROBOTICS_THEME
    ].copy()

    quantum = selection[
        selection[
            "ranking_theme"
        ]
        ==
        QUANTUM_THEME
    ].copy()

    # ------------------------------------------------------------------
    # CONTAGEM
    # ------------------------------------------------------------------

    if len(robotics) != ROBOTICS_TOP_N:

        raise RuntimeError(
            "Arquitetura violada: "
            f"ROBOTICS possui {len(robotics)} "
            "empresas selecionadas; "
            f"esperado = {ROBOTICS_TOP_N}."
        )

    if len(quantum) != QUANTUM_TOP_N:

        raise RuntimeError(
            "Arquitetura violada: "
            f"QUANTUM possui {len(quantum)} "
            "empresas selecionadas; "
            f"esperado = {QUANTUM_TOP_N}."
        )

    # ------------------------------------------------------------------
    # FATOR
    # ------------------------------------------------------------------

    if not (
        robotics[
            "fundamental_factor"
        ]
        ==
        ROBOTICS_FACTOR
    ).all():

        raise RuntimeError(
            "ROBOTICS não está utilizando "
            "Financial Strength."
        )

    if not (
        quantum[
            "fundamental_factor"
        ]
        ==
        QUANTUM_FACTOR
    ).all():

        raise RuntimeError(
            "QUANTUM não está utilizando "
            "Growth."
        )

    # ------------------------------------------------------------------
    # POSIÇÕES
    # ------------------------------------------------------------------

    robotics_positions = (
        robotics[
            "fundamental_position"
        ]
        .astype(int)
        .tolist()
    )

    quantum_positions = (
        quantum[
            "fundamental_position"
        ]
        .astype(int)
        .tolist()
    )

    if sorted(
        robotics_positions
    ) != list(
        range(
            1,
            ROBOTICS_TOP_N + 1,
        )
    ):

        raise RuntimeError(
            "Posições fundamentais de "
            "ROBOTICS inválidas."
        )

    if sorted(
        quantum_positions
    ) != list(
        range(
            1,
            QUANTUM_TOP_N + 1,
        )
    ):

        raise RuntimeError(
            "Posições fundamentais de "
            "QUANTUM inválidas."
        )

    # ------------------------------------------------------------------
    # SELEÇÃO
    # ------------------------------------------------------------------

    if not robotics[
        "selected_fundamentally"
    ].all():

        raise RuntimeError(
            "ROBOTICS contém empresa "
            "não selecionada fundamentalmente."
        )

    if not quantum[
        "selected_fundamentally"
    ].all():

        raise RuntimeError(
            "QUANTUM contém empresa "
            "não selecionada fundamentalmente."
        )


# ======================================================================================
# 12. AUDITORIA
# ======================================================================================

def build_fundamental_audit(
    ranking: pd.DataFrame,
) -> pd.DataFrame:

    if ranking is None or ranking.empty:

        return pd.DataFrame()

    columns = [
        "ticker",
        "ranking_theme",
        "fundamental_position",
        "fundamental_factor",
        "fundamental_score",
        "selected_fundamentally",
    ]

    existing = [
        column
        for column in columns
        if column in ranking.columns
    ]

    return (
        ranking[
            existing
        ]
        .copy()
        .sort_values(
            [
                "ranking_theme",
                "fundamental_position",
            ]
        )
        .reset_index(
            drop=True
        )
    )


# ======================================================================================
# 13. FACHADA DO ENGINE
# ======================================================================================

class FundamentalSelection:

    @staticmethod
    def calculate(
        fundamentals: pd.DataFrame,
        return_full_ranking: bool = False,
    ):

        # Validação da política congelada, se disponível.
        validate_frozen_policy()

        robotics_ranking = (
            rank_robotics(
                fundamentals
            )
        )

        quantum_ranking = (
            rank_quantum(
                fundamentals
            )
        )

        full_ranking = pd.concat(
            [
                robotics_ranking,
                quantum_ranking,
            ],
            ignore_index=True,
        )

        selected = full_ranking[
            full_ranking[
                "selected_fundamentally"
            ]
        ].copy()

        selected = (
            selected
            .sort_values(
                [
                    "ranking_theme",
                    "fundamental_position",
                ]
            )
            .reset_index(
                drop=True
            )
        )

        validate_fundamental_selection(
            selected
        )

        if return_full_ranking:

            return (
                selected,
                full_ranking,
            )

        return selected


# ======================================================================================
# 14. TESTE DIRETO
# ======================================================================================

if __name__ == "__main__":

    print(
        "=" * 100
    )

    print(
        "ROBOTICS_QUANTUM_SP500 "
        "— FUNDAMENTAL SELECTION"
    )

    print(
        "=" * 100
    )

    print(
        "\nArquitetura congelada:"
    )

    print(
        "  ROBOTICS"
    )

    print(
        "    Financial Strength"
    )

    print(
        "    cash_assets ↑"
    )

    print(
        "    debt_assets ↓"
    )

    print(
        "    debt_equity ↓"
    )

    print(
        "    Top 5"
    )

    print(
        "\n  QUANTUM"
    )

    print(
        "    Growth"
    )

    print(
        "    revenue_growth ↑"
    )

    print(
        "    eps_growth ↑"
    )

    print(
        "    operating_cash_flow_growth ↑"
    )

    print(
        "    Top 2"
    )

    print(
        "\n  BOTH participa "
        "independentemente dos dois rankings."
    )

    print(
        "\n  Timing não participa "
        "da seleção fundamental."
    )

    print(
        "\nFundamental Selection "
        "carregado com sucesso."
    )
