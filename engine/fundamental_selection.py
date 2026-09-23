"""
ROBOTICS_QUANTUM_SP500
======================

Motor de seleção fundamental.

POLÍTICA CONGELADA
------------------
ROBOTICS
    Financial Strength
    Top 5

    cash_assets ↑
    debt_assets ↓
    debt_equity ↓

QUANTUM
    Growth
    Top 2

    revenue_growth ↑
    eps_growth ↑
    operating_cash_flow_growth ↑

METODOLOGIA
-----------
1. Separar universo por tema.
2. Utilizar somente componentes fundamentais válidos.
3. Winsorizar P5-P95 dentro do universo temático.
4. Calcular percentis dentro do universo temático.
5. Inverter percentis das métricas em que menor é melhor.
6. Calcular média dos componentes válidos.
7. Exigir no mínimo 2 de 3 componentes.
8. Ordenar pelo score.
9. Selecionar Top 5 Robotics.
10. Selecionar Top 2 Quantum.

IMPORTANTE
----------
Este módulo NÃO usa timing.
Este módulo NÃO usa preço.
Este módulo NÃO usa retorno futuro.
Este módulo NÃO gera venda.
"""

from __future__ import annotations

from typing import Dict, Iterable, List

import numpy as np
import pandas as pd

from config.fundamental_policy import (
    FACTOR_DEFINITIONS,
    THEME_POLICY,
    validate_frozen_policy,
)


# =============================================================================
# CONFIGURAÇÃO
# =============================================================================

WINSOR_LOWER = 0.05
WINSOR_UPPER = 0.95


# =============================================================================
# COLUNAS FUNDAMENTAIS
# =============================================================================

FINANCIAL_STRENGTH_COLUMNS = [
    "cash_assets",
    "debt_assets",
    "debt_equity",
]

GROWTH_COLUMNS = [
    "revenue_growth",
    "eps_growth",
    "operating_cash_flow_growth",
]


# =============================================================================
# VALIDAÇÃO
# =============================================================================

def validate_snapshot(
    snapshot: pd.DataFrame,
) -> bool:
    """
    Valida o snapshot recebido de fundamental_data.py.
    """

    if not isinstance(
        snapshot,
        pd.DataFrame,
    ):
        raise TypeError(
            "snapshot deve ser pandas DataFrame."
        )

    if snapshot.empty:
        raise ValueError(
            "Snapshot fundamental vazio."
        )

    required = {
        "ticker",
        "theme",
        "cash_assets",
        "debt_assets",
        "debt_equity",
        "revenue_growth",
        "eps_growth",
        "operating_cash_flow_growth",
    }

    missing = (
        required
        - set(snapshot.columns)
    )

    if missing:
        raise ValueError(
            "Colunas fundamentais ausentes: "
            f"{sorted(missing)}"
        )

    if snapshot[
        "ticker"
    ].isna().any():
        raise ValueError(
            "Ticker ausente no snapshot."
        )

    if snapshot[
        "ticker"
    ].duplicated().any():
        raise ValueError(
            "Ticker duplicado no snapshot fundamental."
        )

    return True


# =============================================================================
# NORMALIZAÇÃO NUMÉRICA
# =============================================================================

def normalize_numeric_columns(
    df: pd.DataFrame,
) -> pd.DataFrame:
    """
    Converte métricas fundamentais para valores numéricos
    e remove infinitos.
    """

    result = df.copy()

    columns = (
        FINANCIAL_STRENGTH_COLUMNS
        + GROWTH_COLUMNS
    )

    for column in columns:

        result[column] = pd.to_numeric(
            result[column],
            errors="coerce",
        )

        result[column] = (
            result[column]
            .replace(
                [
                    np.inf,
                    -np.inf,
                ],
                np.nan,
            )
        )

    return result


# =============================================================================
# UNIVERSO DE RANKING
# =============================================================================

def build_theme_universe(
    snapshot: pd.DataFrame,
    theme: str,
) -> pd.DataFrame:
    """
    Cria o universo independente utilizado no ranking.

    ROBOTICS:
        ROBOTICS + BOTH

    QUANTUM:
        QUANTUM + BOTH
    """

    theme = str(
        theme
    ).upper()

    if theme == "ROBOTICS":

        allowed = {
            "ROBOTICS",
            "BOTH",
        }

    elif theme == "QUANTUM":

        allowed = {
            "QUANTUM",
            "BOTH",
        }

    else:

        raise ValueError(
            f"Tema inválido: {theme}"
        )

    df = snapshot.loc[
        snapshot["theme"]
        .astype(str)
        .str.upper()
        .isin(
            allowed
        )
    ].copy()

    if df.empty:
        raise RuntimeError(
            f"Universo {theme} vazio."
        )

    df["ranking_theme"] = (
        theme
    )

    return df


# =============================================================================
# WINSORIZAÇÃO
# =============================================================================

def winsorize_series(
    series: pd.Series,
    lower: float = WINSOR_LOWER,
    upper: float = WINSOR_UPPER,
) -> pd.Series:
    """
    Winsorização P5-P95.

    Valores ausentes permanecem ausentes.
    """

    numeric = pd.to_numeric(
        series,
        errors="coerce",
    )

    valid = numeric.dropna()

    if valid.empty:
        return numeric

    if len(valid) == 1:
        return numeric

    lower_bound = valid.quantile(
        lower
    )

    upper_bound = valid.quantile(
        upper
    )

    return numeric.clip(
        lower=lower_bound,
        upper=upper_bound,
    )


# =============================================================================
# SCORE DE FATOR
# =============================================================================

def calculate_factor_score(
    theme_df: pd.DataFrame,
    factor_name: str,
) -> pd.DataFrame:
    """
    Calcula score de um fator exatamente dentro
    do universo temático recebido.

    A maior pontuação é sempre melhor.
    """

    factor_name = str(
        factor_name
    ).upper()

    if factor_name not in FACTOR_DEFINITIONS:
        raise ValueError(
            f"Fator desconhecido: {factor_name}"
        )

    definition = FACTOR_DEFINITIONS[
        factor_name
    ]

    higher = list(
        definition[
            "higher_is_better"
        ]
    )

    lower = list(
        definition[
            "lower_is_better"
        ]
    )

    minimum_components = int(
        definition[
            "minimum_components"
        ]
    )

    metrics = (
        higher
        + lower
    )

    df = theme_df.copy()

    missing = (
        set(metrics)
        - set(df.columns)
    )

    if missing:
        raise ValueError(
            f"Métricas ausentes para {factor_name}: "
            f"{sorted(missing)}"
        )

    score_columns: List[str] = []

    # -------------------------------------------------------------------------
    # HIGHER IS BETTER
    # -------------------------------------------------------------------------

    for metric in higher:

        winsor_column = (
            f"{metric}_winsor"
        )

        percentile_column = (
            f"{metric}_percentile"
        )

        df[winsor_column] = (
            winsorize_series(
                df[metric]
            )
        )

        df[percentile_column] = (
            df[winsor_column]
            .rank(
                pct=True,
                method="average",
            )
        )

        score_columns.append(
            percentile_column
        )

    # -------------------------------------------------------------------------
    # LOWER IS BETTER
    # -------------------------------------------------------------------------

    for metric in lower:

        winsor_column = (
            f"{metric}_winsor"
        )

        percentile_column = (
            f"{metric}_percentile"
        )

        df[winsor_column] = (
            winsorize_series(
                df[metric]
            )
        )

        raw_percentile = (
            df[winsor_column]
            .rank(
                pct=True,
                method="average",
            )
        )

        # Menor valor fundamental = maior score.

        df[percentile_column] = (
            1.0
            - raw_percentile
            + (1.0 / raw_percentile.count())
            if raw_percentile.count() > 0
            else raw_percentile
        )

        score_columns.append(
            percentile_column
        )

    # -------------------------------------------------------------------------
    # QUANTIDADE DE COMPONENTES VÁLIDOS
    # -------------------------------------------------------------------------

    component_count_column = (
        f"{factor_name.lower()}_components"
    )

    score_column = (
        f"{factor_name.lower()}_score"
    )

    df[
        component_count_column
    ] = (
        df[
            score_columns
        ]
        .notna()
        .sum(
            axis=1
        )
    )

    # -------------------------------------------------------------------------
    # MÉDIA DOS COMPONENTES VÁLIDOS
    # -------------------------------------------------------------------------

    df[
        score_column
    ] = (
        df[
            score_columns
        ]
        .mean(
            axis=1,
            skipna=True,
        )
    )

    # -------------------------------------------------------------------------
    # MÍNIMO DE COMPONENTES
    # -------------------------------------------------------------------------

    insufficient = (
        df[
            component_count_column
        ]
        < minimum_components
    )

    df.loc[
        insufficient,
        score_column,
    ] = np.nan

    df[
        f"{factor_name.lower()}_eligible"
    ] = (
        ~insufficient
        & df[
            score_column
        ].notna()
    )

    return df


# =============================================================================
# RANKING
# =============================================================================

def rank_factor(
    scored: pd.DataFrame,
    factor_name: str,
) -> pd.DataFrame:
    """
    Ordena empresas pelo score fundamental.
    """

    factor_name = str(
        factor_name
    ).upper()

    score_column = (
        f"{factor_name.lower()}_score"
    )

    eligible_column = (
        f"{factor_name.lower()}_eligible"
    )

    if score_column not in scored.columns:
        raise ValueError(
            f"Score ausente: {score_column}"
        )

    df = scored.loc[
        scored[
            eligible_column
        ]
    ].copy()

    if df.empty:
        raise RuntimeError(
            f"Nenhuma empresa elegível "
            f"para {factor_name}."
        )

    # Critério primário:
    # maior score.
    #
    # Ticker serve apenas como desempate
    # determinístico operacional.

    df = (
        df
        .sort_values(
            by=[
                score_column,
                "ticker",
            ],
            ascending=[
                False,
                True,
            ],
            kind="mergesort",
        )
        .reset_index(
            drop=True
        )
    )

    # position é sequencial.
    # Isso evita reduzir o número selecionado
    # quando existem empates de score.

    df[
        "fundamental_position"
    ] = (
        np.arange(
            1,
            len(df) + 1,
        )
    )

    # Rank estatístico preservado
    # para auditoria de empates.

    df[
        "fundamental_rank"
    ] = (
        df[
            score_column
        ]
        .rank(
            ascending=False,
            method="min",
        )
        .astype(int)
    )

    return df


# =============================================================================
# SELEÇÃO DE UM TEMA
# =============================================================================

def select_theme(
    snapshot: pd.DataFrame,
    theme: str,
) -> pd.DataFrame:
    """
    Executa a política fundamental congelada
    de um tema.
    """

    theme = str(
        theme
    ).upper()

    if theme not in THEME_POLICY:
        raise ValueError(
            f"Tema sem política: {theme}"
        )

    policy = THEME_POLICY[
        theme
    ]

    factor = str(
        policy[
            "factor"
        ]
    ).upper()

    top_n = int(
        policy[
            "top_n"
        ]
    )

    universe = (
        build_theme_universe(
            snapshot,
            theme,
        )
    )

    scored = (
        calculate_factor_score(
            universe,
            factor,
        )
    )

    ranked = (
        rank_factor(
            scored,
            factor,
        )
    )

    selected = (
        ranked
        .head(
            top_n
        )
        .copy()
    )

    selected[
        "fundamental_factor"
    ] = factor

    selected[
        "fundamental_score"
    ] = selected[
        f"{factor.lower()}_score"
    ]

    selected[
        "selected_fundamentally"
    ] = True

    selected[
        "top_n_policy"
    ] = top_n

    selected[
        "fundamental_evidence"
    ] = policy.get(
        "evidence"
    )

    if len(selected) > top_n:
        raise AssertionError(
            f"{theme}: seleção excedeu Top {top_n}."
        )

    return selected


# =============================================================================
# ROBOTICS
# =============================================================================

def select_robotics(
    snapshot: pd.DataFrame,
) -> pd.DataFrame:
    """
    Financial Strength -> Top 5.
    """

    result = select_theme(
        snapshot,
        "ROBOTICS",
    )

    if (
        result[
            "fundamental_factor"
        ]
        != "FINANCIAL_STRENGTH"
    ).any():
        raise AssertionError(
            "Robotics utilizou fator incorreto."
        )

    if len(result) > 5:
        raise AssertionError(
            "Robotics excedeu Top 5."
        )

    return result


# =============================================================================
# QUANTUM
# =============================================================================

def select_quantum(
    snapshot: pd.DataFrame,
) -> pd.DataFrame:
    """
    Growth -> Top 2.
    """

    result = select_theme(
        snapshot,
        "QUANTUM",
    )

    if (
        result[
            "fundamental_factor"
        ]
        != "GROWTH"
    ).any():
        raise AssertionError(
            "Quantum utilizou fator incorreto."
        )

    if len(result) > 2:
        raise AssertionError(
            "Quantum excedeu Top 2."
        )

    return result


# =============================================================================
# SELEÇÃO COMPLETA
# =============================================================================

def select_fundamental_portfolio(
    snapshot: pd.DataFrame,
) -> Dict[str, pd.DataFrame]:
    """
    Executa os dois motores fundamentais.

    ROBOTICS:
        Financial Strength -> Top 5

    QUANTUM:
        Growth -> Top 2
    """

    validate_frozen_policy()

    validate_snapshot(
        snapshot
    )

    normalized = (
        normalize_numeric_columns(
            snapshot
        )
    )

    robotics = (
        select_robotics(
            normalized
        )
    )

    quantum = (
        select_quantum(
            normalized
        )
    )

    validate_final_selection(
        robotics=robotics,
        quantum=quantum,
    )

    return {
        "ROBOTICS":
            robotics,

        "QUANTUM":
            quantum,
    }


# =============================================================================
# AUDITORIA FINAL
# =============================================================================

def validate_final_selection(
    robotics: pd.DataFrame,
    quantum: pd.DataFrame,
) -> bool:
    """
    Garante que a política congelada não sofreu drift.
    """

    if len(robotics) > 5:
        raise AssertionError(
            "Mais de 5 empresas selecionadas "
            "em Robotics."
        )

    if len(quantum) > 2:
        raise AssertionError(
            "Mais de 2 empresas selecionadas "
            "em Quantum."
        )

    if not robotics.empty:

        if (
            robotics[
                "ranking_theme"
            ]
            != "ROBOTICS"
        ).any():

            raise AssertionError(
                "Empresa não-Robotics "
                "entrou no ranking Robotics."
            )

        if (
            robotics[
                "fundamental_factor"
            ]
            != "FINANCIAL_STRENGTH"
        ).any():

            raise AssertionError(
                "Fator Robotics foi alterado."
            )

    if not quantum.empty:

        if (
            quantum[
                "ranking_theme"
            ]
            != "QUANTUM"
        ).any():

            raise AssertionError(
                "Empresa não-Quantum "
                "entrou no ranking Quantum."
            )

        if (
            quantum[
                "fundamental_factor"
            ]
            != "GROWTH"
        ).any():

            raise AssertionError(
                "Fator Quantum foi alterado."
            )

    return True


# =============================================================================
# CONSOLIDAÇÃO
# =============================================================================

def consolidate_selection(
    selections: Dict[str, pd.DataFrame],
) -> pd.DataFrame:
    """
    Consolida Robotics e Quantum mantendo
    as duas participações de uma empresa BOTH.

    Exemplo:
        NVDA pode aparecer uma vez como Robotics
        e uma vez como Quantum.

    A deduplicação da empresa final ocorrerá
    posteriormente no portfolio_engine.
    """

    frames = []

    for theme in (
        "ROBOTICS",
        "QUANTUM",
    ):

        df = selections.get(
            theme
        )

        if (
            df is None
            or df.empty
        ):
            continue

        frames.append(
            df.copy()
        )

    if not frames:
        raise RuntimeError(
            "Nenhuma seleção fundamental produzida."
        )

    result = pd.concat(
        frames,
        ignore_index=True,
    )

    result = (
        result
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

    return result


# =============================================================================
# RELATÓRIO DE CONSOLE
# =============================================================================

def print_selection(
    selections: Dict[str, pd.DataFrame],
) -> None:
    """
    Exibe seleção fundamental atual.
    """

    print(
        "=" * 110
    )

    print(
        "ROBOTICS_QUANTUM_SP500 — "
        "SELEÇÃO FUNDAMENTAL"
    )

    print(
        "=" * 110
    )

    for theme in (
        "ROBOTICS",
        "QUANTUM",
    ):

        df = selections[
            theme
        ]

        print(
            f"\n{theme}"
        )

        print(
            "-" * 110
        )

        if df.empty:

            print(
                "Nenhuma empresa selecionada."
            )

            continue

        print(
            df[
                [
                    "fundamental_position",
                    "fundamental_rank",
                    "ticker",
                    "company",
                    "theme",
                    "fundamental_factor",
                    "fundamental_score",
                    "gics_sector",
                ]
            ].to_string(
                index=False
            )
        )
