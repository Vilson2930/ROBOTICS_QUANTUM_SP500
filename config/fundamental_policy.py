"""
ROBOTICS_QUANTUM_SP500
======================

Política fundamental oficial do robô.

Esta política foi congelada após o estudo quantitativo.

ROBOTICS
--------
Fator: Financial Strength
Seleção: Top 5

Componentes:
- cash_assets: maior é melhor
- debt_assets: menor é melhor
- debt_equity: menor é melhor

QUANTUM
-------
Fator: Growth
Seleção: Top 2

Componentes:
- revenue_growth: maior é melhor
- eps_growth: maior é melhor
- operating_cash_flow_growth: maior é melhor

IMPORTANTE:
Este arquivo define a política.
O cálculo será executado pelo fundamental_selection.py.
"""

from config.settings import (
    ROBOTICS_FACTOR,
    ROBOTICS_TOP_N,
    ROBOTICS_MIN_COMPONENTS,
    ROBOTICS_FINANCIAL_STRENGTH_HIGHER_IS_BETTER,
    ROBOTICS_FINANCIAL_STRENGTH_LOWER_IS_BETTER,
    QUANTUM_FACTOR,
    QUANTUM_TOP_N,
    QUANTUM_MIN_COMPONENTS,
    QUANTUM_GROWTH_HIGHER_IS_BETTER,
)


# =============================================================================
# DEFINIÇÕES DOS FATORES
# =============================================================================
#
# IMPORTANTE:
# As chaves e os nomes internos abaixo seguem exatamente a interface
# utilizada pelo fundamental_selection.py:
#
#   financial_strength
#   growth
#
# e:
#
#   higher
#   lower
#   minimum_components
#
# A nomenclatura em minúsculas é uma interface técnica.
# Ela NÃO altera a política fundamental congelada.
# =============================================================================

FACTOR_DEFINITIONS = {

    "financial_strength": {

        "higher": list(
            ROBOTICS_FINANCIAL_STRENGTH_HIGHER_IS_BETTER
        ),

        "lower": list(
            ROBOTICS_FINANCIAL_STRENGTH_LOWER_IS_BETTER
        ),

        "minimum_components":
            ROBOTICS_MIN_COMPONENTS,
    },

    "growth": {

        "higher": list(
            QUANTUM_GROWTH_HIGHER_IS_BETTER
        ),

        "lower": [],

        "minimum_components":
            QUANTUM_MIN_COMPONENTS,
    },
}


# =============================================================================
# POLÍTICA POR TEMA
# =============================================================================

THEME_POLICY = {

    "ROBOTICS": {

        "factor":
            ROBOTICS_FACTOR,

        "top_n":
            ROBOTICS_TOP_N,

        "timing":
            "AI_INFRASTRUCTURE_SIGNAL_ENGINE",

        "timing_enabled":
            True,

        "evidence":
            "STRONG",
    },

    "QUANTUM": {

        "factor":
            QUANTUM_FACTOR,

        "top_n":
            QUANTUM_TOP_N,

        "timing":
            None,

        "timing_enabled":
            False,

        "evidence":
            "MODERATE",
    },
}


# =============================================================================
# EMPRESAS CLASSIFICADAS COMO BOTH
# =============================================================================
#
# Uma empresa BOTH participa independentemente dos dois rankings.
#
# Exemplo:
#
# NVDA pode estar:
# - no Top 5 Robotics;
# - no Top 2 Quantum;
# - ou em ambos.
#
# Uma classificação não interfere na outra.
# =============================================================================

BOTH_POLICY = {

    "participates_in_robotics":
        True,

    "participates_in_quantum":
        True,

    "rank_independently":
        True,

    "deduplicate_final_company":
        True,

    "preserve_theme_memberships":
        True,
}


# =============================================================================
# POLÍTICA DE SELEÇÃO
# =============================================================================

SELECTION_POLICY = {

    "ROBOTICS": {

        "factor":
            "FINANCIAL_STRENGTH",

        "top_n":
            5,

        "higher_is_better": [
            "cash_assets",
        ],

        "lower_is_better": [
            "debt_assets",
            "debt_equity",
        ],

        "minimum_components":
            2,
    },

    "QUANTUM": {

        "factor":
            "GROWTH",

        "top_n":
            2,

        "higher_is_better": [
            "revenue_growth",
            "eps_growth",
            "operating_cash_flow_growth",
        ],

        "lower_is_better": [],

        "minimum_components":
            2,
    },
}


# =============================================================================
# REGRAS DE RANKING
# =============================================================================

RANKING_POLICY = {

    "winsorization":
        True,

    "winsorization_lower":
        0.05,

    "winsorization_upper":
        0.95,

    "percentile_ranking":
        True,

    "score_method":
        "MEAN_VALID_COMPONENTS",

    "highest_score_is_best":
        True,
}


# =============================================================================
# PROTEÇÕES
# =============================================================================

PROTECTION_POLICY = {

    "timing_can_change_selection":
        False,

    "timing_can_change_rank":
        False,

    "timing_can_generate_sell":
        False,

    "price_drop_can_generate_sell":
        False,

    "future_returns_allowed":
        False,

    "lookahead_allowed":
        False,
}


# =============================================================================
# FUNÇÕES AUXILIARES
# =============================================================================

def normalize_factor_name(
    factor_name,
):
    """
    Converte o nome público/configurado do fator
    para a chave técnica utilizada pelo motor.

    Exemplos:
        FINANCIAL_STRENGTH -> financial_strength
        GROWTH             -> growth
    """

    return (
        str(factor_name)
        .strip()
        .lower()
    )


def get_factor_definition(
    factor_name,
):
    """
    Retorna a definição oficial de um fator.
    """

    factor_name = normalize_factor_name(
        factor_name
    )

    if factor_name not in FACTOR_DEFINITIONS:

        raise ValueError(
            f"Fator não autorizado: "
            f"{factor_name}"
        )

    return FACTOR_DEFINITIONS[
        factor_name
    ]


def get_theme_policy(
    theme,
):
    """
    Retorna a política oficial de um tema.
    """

    theme = (
        str(theme)
        .strip()
        .upper()
    )

    if theme not in THEME_POLICY:

        raise ValueError(
            f"Tema não autorizado: "
            f"{theme}"
        )

    return THEME_POLICY[
        theme
    ]


def get_top_n(
    theme,
):
    """
    Retorna o número oficial de empresas
    selecionadas para o tema.
    """

    return int(
        get_theme_policy(
            theme
        )[
            "top_n"
        ]
    )


def get_factor_for_theme(
    theme,
):
    """
    Retorna o fator oficial utilizado pelo tema.

    Mantém o nome oficial definido em settings.py.
    """

    return str(
        get_theme_policy(
            theme
        )[
            "factor"
        ]
    )


# =============================================================================
# VALIDAÇÃO DA POLÍTICA CONGELADA
# =============================================================================

def validate_frozen_policy():
    """
    Impede alterações acidentais na arquitetura
    validada pelo estudo.
    """

    # -------------------------------------------------------------------------
    # Política oficial
    # -------------------------------------------------------------------------

    assert ROBOTICS_FACTOR == (
        "FINANCIAL_STRENGTH"
    )

    assert ROBOTICS_TOP_N == 5

    assert ROBOTICS_MIN_COMPONENTS == 2

    assert QUANTUM_FACTOR == (
        "GROWTH"
    )

    assert QUANTUM_TOP_N == 2

    assert QUANTUM_MIN_COMPONENTS == 2

    # -------------------------------------------------------------------------
    # Interface técnica dos fatores
    # -------------------------------------------------------------------------

    assert (
        normalize_factor_name(
            ROBOTICS_FACTOR
        )
        ==
        "financial_strength"
    )

    assert (
        normalize_factor_name(
            QUANTUM_FACTOR
        )
        ==
        "growth"
    )

    assert (
        "financial_strength"
        in
        FACTOR_DEFINITIONS
    )

    assert (
        "growth"
        in
        FACTOR_DEFINITIONS
    )

    robotics = (
        FACTOR_DEFINITIONS[
            "financial_strength"
        ]
    )

    quantum = (
        FACTOR_DEFINITIONS[
            "growth"
        ]
    )

    # -------------------------------------------------------------------------
    # Financial Strength
    # -------------------------------------------------------------------------

    assert robotics[
        "higher"
    ] == [
        "cash_assets"
    ]

    assert robotics[
        "lower"
    ] == [
        "debt_assets",
        "debt_equity",
    ]

    assert robotics[
        "minimum_components"
    ] == 2

    # -------------------------------------------------------------------------
    # Growth
    # -------------------------------------------------------------------------

    assert quantum[
        "higher"
    ] == [
        "revenue_growth",
        "eps_growth",
        "operating_cash_flow_growth",
    ]

    assert quantum[
        "lower"
    ] == []

    assert quantum[
        "minimum_components"
    ] == 2

    # -------------------------------------------------------------------------
    # BOTH
    # -------------------------------------------------------------------------

    assert BOTH_POLICY[
        "participates_in_robotics"
    ] is True

    assert BOTH_POLICY[
        "participates_in_quantum"
    ] is True

    assert BOTH_POLICY[
        "rank_independently"
    ] is True

    assert BOTH_POLICY[
        "deduplicate_final_company"
    ] is True

    assert BOTH_POLICY[
        "preserve_theme_memberships"
    ] is True

    # -------------------------------------------------------------------------
    # Proteções da arquitetura
    # -------------------------------------------------------------------------

    assert PROTECTION_POLICY[
        "timing_can_change_selection"
    ] is False

    assert PROTECTION_POLICY[
        "timing_can_change_rank"
    ] is False

    assert PROTECTION_POLICY[
        "timing_can_generate_sell"
    ] is False

    assert PROTECTION_POLICY[
        "price_drop_can_generate_sell"
    ] is False

    assert PROTECTION_POLICY[
        "future_returns_allowed"
    ] is False

    assert PROTECTION_POLICY[
        "lookahead_allowed"
    ] is False

    return True


# =============================================================================
# EXECUTAR VALIDAÇÃO AO IMPORTAR
# =============================================================================

validate_frozen_policy()
