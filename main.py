"""
ROBOTICS_QUANTUM_SP500
======================

Orquestrador principal.

ARQUITETURA CONGELADA

S&P 500
    ↓
Classificação Robotics / Quantum
    ↓
Fundamentos Point-in-Time
    ↓
Seleção Fundamental
    ├── ROBOTICS -> Financial Strength -> Top 5
    └── QUANTUM  -> Growth -> Top 2
    ↓
ROBOTICS ONLY
    Market Data
    Technical Indicators
    Institutional Score
    Technical Score
    Entry Timing Engine
    Signal Engine
    ↓
Portfolio Engine
    ↓
Report Generator

REGRAS
------
- Fundamental decide quais empresas pertencem à seleção.
- Timing somente avalia entrada/aporte em Robotics.
- Timing não altera ranking fundamental.
- Timing não gera venda.
- Quantum não utiliza timing técnico.
"""

from __future__ import annotations

import sys
import traceback
from datetime import datetime, timezone

import pandas as pd

from config.settings import (
    PROJECT_NAME,
    VERSION,
)

from data.sp500_universe import (
    get_sp500_universe,
)

from engine.thematic_classifier import (
    ThematicClassifier,
)

from data.fundamental_data import (
    FundamentalData,
)

from engine.fundamental_selection import (
    FundamentalSelection,
)

from data.market_data import (
    get_robotics_market_data,
    attach_real_gics,
)

from engine.technical_indicators import (
    TechnicalIndicators,
)

from engine.institutional_score import (
    InstitutionalScore,
)

from engine.technical_score import (
    TechnicalScore,
)

from engine.entry_timing_engine import (
    EntryTimingEngine,
)

from engine.signal_engine import (
    SignalEngine,
)

from engine.portfolio_engine import (
    PortfolioEngine,
)

from reports.report_generator import (
    ReportGenerator,
)


# ============================================================
# CONFIGURAÇÃO DE EXECUÇÃO
# ============================================================

SAVE_INTERMEDIATE_FILES = True


# ============================================================
# AUXILIARES
# ============================================================

def print_header() -> None:

    print("=" * 120)
    print(PROJECT_NAME.upper())
    print(f"VERSÃO {VERSION}")
    print("=" * 120)

    print(
        "Objetivo: selecionar as melhores empresas do S&P 500 "
        "ligadas a Robotics e Quantum Computing."
    )

    print(
        "Robotics: Financial Strength Top 5 "
        "+ timing do AI Infrastructure Scanner."
    )

    print(
        "Quantum: Growth Top 2 "
        "+ seleção exclusivamente fundamental."
    )

    print("=" * 120)

    print(
        "Início: "
        f"{datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}"
    )

    print("=" * 120)


def print_stage(
    number: int,
    title: str,
) -> None:

    print()
    print("=" * 120)

    print(
        f"ETAPA {number} — {title}"
    )

    print("=" * 120)


def validate_dataframe(
    data: pd.DataFrame,
    name: str,
) -> None:

    if not isinstance(
        data,
        pd.DataFrame,
    ):
        raise TypeError(
            f"{name} não é DataFrame."
        )

    if data.empty:
        raise ValueError(
            f"{name} está vazio."
        )

    print(
        f"{name}: {len(data):,} linhas"
    )


# ============================================================
# INTEGRAÇÃO TIMING -> TECHNICAL SCORE
# ============================================================

def merge_timing_into_technical(
    technical_ranking: pd.DataFrame,
    timing_ranking: pd.DataFrame,
) -> pd.DataFrame:
    """
    Replica a arquitetura do AI Infrastructure Scanner:

    Technical Score
        +
    Entry Timing Engine
        ↓
    Signal Engine
    """

    timing_columns = [
        "ticker",
        "entry_timing_score",
        "timing_status",
        "timing_approved",
        "pullback_probability",
        "parabolic_risk",
        "timing_confidence",
        "timing_confirmations",
        "timing_positive_factors",
        "timing_pending_conditions",
        "timing_rejection_reasons",
        "timing_decision",
        "retorno_5d",
        "retorno_10d",
        "distancia_sma_10",
        "distancia_maxima_20d",
        "volume_relativo_5d",
        "weekly_extension_risk",
        "parabolic_move_risk",
        "pullback_required",
        "extension_score",
    ]

    available_timing_columns = [
        column
        for column in timing_columns
        if column in timing_ranking.columns
    ]

    if "ticker" not in available_timing_columns:
        raise KeyError(
            "Entry Timing Engine não retornou ticker."
        )

    result = (
        technical_ranking
        .merge(
            timing_ranking[
                available_timing_columns
            ],
            on="ticker",
            how="left",
            validate="one_to_one",
        )
    )

    # Mesmo comportamento do scanner original:
    # em eventual duplicidade, preserva a versão mais recente
    # incorporada pelo timing.

    result = (
        result.loc[
            :,
            ~result.columns.duplicated(
                keep="last"
            ),
        ]
        .copy()
    )

    return result


# ============================================================
# PIPELINE
# ============================================================

def run() -> dict:
    """
    Executa o robô completo.
    """

    print_header()

    # ========================================================
    # 1 — S&P 500
    # ========================================================

    print_stage(
        1,
        "ATUALIZAÇÃO DO UNIVERSO S&P 500",
    )

    sp500 = (
        get_sp500_universe()
    )

    validate_dataframe(
        sp500,
        "Universo S&P 500",
    )

    # ========================================================
    # 2 — CLASSIFICAÇÃO TEMÁTICA
    # ========================================================

    print_stage(
        2,
        "CLASSIFICAÇÃO ROBOTICS / QUANTUM",
    )

    thematic_engine = (
        ThematicClassifier()
    )

    thematic_universe = (
        thematic_engine.calculate(
            sp500
        )
    )

    validate_dataframe(
        thematic_universe,
        "Universo temático",
    )

    # ========================================================
    # 3 — FUNDAMENTOS
    # ========================================================

    print_stage(
        3,
        "FUNDAMENTOS POINT-IN-TIME",
    )

    fundamental_engine = (
        FundamentalData()
    )

    fundamentals = (
        fundamental_engine.calculate(
            thematic_universe
        )
    )

    validate_dataframe(
        fundamentals,
        "Fundamentos",
    )

    # ========================================================
    # 4 — SELEÇÃO FUNDAMENTAL
    # ========================================================

    print_stage(
        4,
        "SELEÇÃO FUNDAMENTAL",
    )

    selection_engine = (
        FundamentalSelection()
    )

    fundamental_selection = (
        selection_engine.calculate(
            fundamentals
        )
    )

    validate_dataframe(
        fundamental_selection,
        "Seleção fundamental",
    )

    robotics_selection = (
        fundamental_selection.loc[
            (
                fundamental_selection[
                    "ranking_theme"
                ]
                .astype(str)
                .str.upper()
                ==
                "ROBOTICS"
            )
            &
            (
                fundamental_selection[
                    "selected_fundamentally"
                ]
                .fillna(False)
                .astype(bool)
            )
        ]
        .copy()
    )

    quantum_selection = (
        fundamental_selection.loc[
            (
                fundamental_selection[
                    "ranking_theme"
                ]
                .astype(str)
                .str.upper()
                ==
                "QUANTUM"
            )
            &
            (
                fundamental_selection[
                    "selected_fundamentally"
                ]
                .fillna(False)
                .astype(bool)
            )
        ]
        .copy()
    )

    if len(robotics_selection) != 5:
        raise AssertionError(
            "A arquitetura exige exatamente "
            f"5 Robotics selecionadas. Obtidas: {len(robotics_selection)}"
        )

    if len(quantum_selection) != 2:
        raise AssertionError(
            "A arquitetura exige exatamente "
            f"2 Quantum selecionadas. Obtidas: {len(quantum_selection)}"
        )

    print()
    print("ROBOTICS — TOP 5")

    print(
        robotics_selection[
            [
                "fundamental_position",
                "ticker",
                "fundamental_score",
            ]
        ]
        .sort_values(
            "fundamental_position"
        )
        .to_string(
            index=False
        )
    )

    print()
    print("QUANTUM — TOP 2")

    print(
        quantum_selection[
            [
                "fundamental_position",
                "ticker",
                "fundamental_score",
            ]
        ]
        .sort_values(
            "fundamental_position"
        )
        .to_string(
            index=False
        )
    )

    # ========================================================
    # 5 — MARKET DATA
    # ========================================================

    print_stage(
        5,
        "MARKET DATA — ROBOTICS TOP 5",
    )

    price_history = (
        get_robotics_market_data(
            fundamental_selection
        )
    )

    price_history = (
        attach_real_gics(
            price_history=
                price_history,

            fundamental_selection=
                robotics_selection,
        )
    )

    validate_dataframe(
        price_history,
        "Histórico Robotics",
    )

    # ========================================================
    # 6 — TECHNICAL INDICATORS
    # ========================================================

    print_stage(
        6,
        "TECHNICAL INDICATORS",
    )

    indicator_engine = (
        TechnicalIndicators()
    )

    indicator_history = (
        indicator_engine.calculate(
            price_history=
                price_history,

            save=
                SAVE_INTERMEDIATE_FILES,
        )
    )

    validate_dataframe(
        indicator_history,
        "Indicadores técnicos",
    )

    # ========================================================
    # 7 — INSTITUTIONAL SCORE
    # ========================================================

    print_stage(
        7,
        "INSTITUTIONAL SCORE",
    )

    institutional_engine = (
        InstitutionalScore()
    )

    institutional_ranking = (
        institutional_engine.calculate(
            indicators=
                indicator_history,

            save=
                SAVE_INTERMEDIATE_FILES,
        )
    )

    validate_dataframe(
        institutional_ranking,
        "Institutional Score",
    )

    # ========================================================
    # 8 — TECHNICAL SCORE
    # ========================================================

    print_stage(
        8,
        "TECHNICAL ENTRY SCORE",
    )

    technical_engine = (
        TechnicalScore()
    )

    technical_ranking = (
        technical_engine.calculate(
            indicators=
                indicator_history,

            save=
                SAVE_INTERMEDIATE_FILES,
        )
    )

    validate_dataframe(
        technical_ranking,
        "Technical Score",
    )

    # ========================================================
    # 9 — ENTRY TIMING ENGINE
    # ========================================================

    print_stage(
        9,
        "ENTRY TIMING ENGINE",
    )

    timing_engine = (
        EntryTimingEngine()
    )

    timing_ranking = (
        timing_engine.calculate(
            indicators=
                indicator_history,

            save=
                SAVE_INTERMEDIATE_FILES,
        )
    )

    validate_dataframe(
        timing_ranking,
        "Entry Timing",
    )

    # ========================================================
    # 10 — INTEGRAÇÃO TECHNICAL + TIMING
    # ========================================================

    print_stage(
        10,
        "INTEGRAÇÃO TECHNICAL SCORE + TIMING",
    )

    technical_with_timing = (
        merge_timing_into_technical(
            technical_ranking=
                technical_ranking,

            timing_ranking=
                timing_ranking,
        )
    )

    validate_dataframe(
        technical_with_timing,
        "Technical + Timing",
    )

    # ========================================================
    # 11 — SIGNAL ENGINE
    # ========================================================

    print_stage(
        11,
        "AI INFRASTRUCTURE SIGNAL ENGINE",
    )

    signal_engine = (
        SignalEngine()
    )

    robotics_signals = (
        signal_engine.calculate(
            institutional_data=
                institutional_ranking,

            technical_data=
                technical_with_timing,

            save=
                SAVE_INTERMEDIATE_FILES,
        )
    )

    validate_dataframe(
        robotics_signals,
        "Robotics Signal Engine",
    )

    # ========================================================
    # PROTEÇÃO DA ARQUITETURA
    # ========================================================

    selected_robotics = set(
        robotics_selection[
            "ticker"
        ]
        .astype(str)
        .str.upper()
    )

    signal_robotics = set(
        robotics_signals[
            "ticker"
        ]
        .astype(str)
        .str.upper()
    )

    unexpected = (
        signal_robotics
        -
        selected_robotics
    )

    if unexpected:
        raise AssertionError(
            "Signal Engine recebeu empresa fora "
            "do Top 5 Robotics: "
            f"{sorted(unexpected)}"
        )

    # ========================================================
    # 12 — PORTFOLIO ENGINE
    # ========================================================

    print_stage(
        12,
        "PORTFOLIO ENGINE",
    )

    portfolio_engine = (
        PortfolioEngine()
    )

    portfolio = (
        portfolio_engine.calculate(
            fundamental_selection=
                fundamental_selection.loc[
                    fundamental_selection[
                        "selected_fundamentally"
                    ]
                    .fillna(False)
                    .astype(bool)
                ]
                .copy(),

            robotics_signal_data=
                robotics_signals,
        )
    )

    validate_dataframe(
        portfolio,
        "Portfólio final",
    )

    # ========================================================
    # 13 — RELATÓRIO
    # ========================================================

    print_stage(
        13,
        "RELATÓRIO FINAL",
    )

    report_engine = (
        ReportGenerator()
    )

    # --------------------------------------------------------
    # CORREÇÃO:
    #
    # ReportGenerator.generate() recebe somente portfolio.
    # Os relatórios são salvos pelo próprio ReportGenerator.
    # --------------------------------------------------------

    report = (
        report_engine.generate(
            portfolio=
                portfolio,
        )
    )

    # ========================================================
    # 14 — AUDITORIA FINAL
    # ========================================================

    print_stage(
        14,
        "AUDITORIA DA ARQUITETURA",
    )

    final_robotics = (
        portfolio.loc[
            portfolio[
                "ranking_theme"
            ]
            .astype(str)
            .str.upper()
            ==
            "ROBOTICS"
        ]
    )

    final_quantum = (
        portfolio.loc[
            portfolio[
                "ranking_theme"
            ]
            .astype(str)
            .str.upper()
            ==
            "QUANTUM"
        ]
    )

    assert len(
        final_robotics
    ) == 5

    assert len(
        final_quantum
    ) == 2

    assert (
        final_robotics[
            "fundamental_factor"
        ]
        .astype(str)
        .str.upper()
        ==
        "FINANCIAL_STRENGTH"
    ).all()

    assert (
        final_quantum[
            "fundamental_factor"
        ]
        .astype(str)
        .str.upper()
        ==
        "GROWTH"
    ).all()

    assert not (
        final_robotics[
            "timing_changes_ownership"
        ]
        .fillna(False)
        .astype(bool)
        .any()
    )

    assert not (
        final_robotics[
            "timing_generates_sell"
        ]
        .fillna(False)
        .astype(bool)
        .any()
    )

    assert not (
        final_robotics[
            "timing_changes_fundamental_rank"
        ]
        .fillna(False)
        .astype(bool)
        .any()
    )

    assert (
        final_quantum[
            "timing_engine"
        ]
        .astype(str)
        .str.upper()
        ==
        "NONE"
    ).all()

    print(
        "S&P 500 obrigatório: OK"
    )

    print(
        "Robotics Financial Strength Top 5: OK"
    )

    print(
        "Quantum Growth Top 2: OK"
    )

    print(
        "Timing somente Robotics: OK"
    )

    print(
        "Timing não altera ownership: OK"
    )

    print(
        "Timing não altera ranking fundamental: OK"
    )

    print(
        "Timing não gera venda: OK"
    )

    print(
        "Quantum sem timing técnico: OK"
    )

    print()
    print("=" * 120)

    print(
        "EXECUÇÃO CONCLUÍDA COM SUCESSO"
    )

    print("=" * 120)

    return {
        "sp500":
            sp500,

        "thematic_universe":
            thematic_universe,

        "fundamentals":
            fundamentals,

        "fundamental_selection":
            fundamental_selection,

        "price_history":
            price_history,

        "indicator_history":
            indicator_history,

        "institutional_ranking":
            institutional_ranking,

        "technical_ranking":
            technical_ranking,

        "timing_ranking":
            timing_ranking,

        "robotics_signals":
            robotics_signals,

        "portfolio":
            portfolio,

        "report":
            report,
    }


# ============================================================
# EXECUÇÃO
# ============================================================

def main() -> int:

    try:

        run()

        return 0

    except Exception as error:

        print()
        print("=" * 120)

        print(
            "ERRO NA EXECUÇÃO DO ROBÔ"
        )

        print("=" * 120)

        print(
            f"{type(error).__name__}: {error}"
        )

        print()
        traceback.print_exc()

        return 1


if __name__ == "__main__":

    sys.exit(
        main()
    )
