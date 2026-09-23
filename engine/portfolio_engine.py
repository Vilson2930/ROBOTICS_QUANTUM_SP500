"""
ROBOTICS_QUANTUM_SP500
======================

Portfolio Engine.

Responsável por consolidar:

1. ROBOTICS
   Financial Strength -> Top 5
   +
   AI Infrastructure Signal Engine -> timing de entrada/aporte

2. QUANTUM
   Growth -> Top 2
   +
   sem timing técnico

REGRA CENTRAL
-------------
O FUNDAMENTAL decide quais empresas são selecionadas.

O TIMING apenas informa o momento de entrada/aporte
das empresas ROBOTICS já selecionadas.

O timing:
- NÃO altera ranking fundamental;
- NÃO remove empresa selecionada;
- NÃO adiciona empresa não selecionada;
- NÃO gera venda;
- NÃO altera Quantum.

A saída de uma empresa ocorre somente quando ela deixa
de pertencer ao Top-N fundamental em uma execução futura.
"""

from __future__ import annotations

from typing import Dict, Optional

import numpy as np
import pandas as pd


ROBOTICS_THEME = "ROBOTICS"
QUANTUM_THEME = "QUANTUM"

ROBOTICS_TOP_N = 5
QUANTUM_TOP_N = 2


# ============================================================
# AUXILIARES
# ============================================================

def _normalize_ticker(
    value,
) -> str:
    """
    Normaliza ticker.
    """

    return (
        str(value)
        .strip()
        .upper()
    )


def _validate_dataframe(
    df: pd.DataFrame,
    name: str,
) -> None:
    """
    Validação básica.
    """

    if not isinstance(
        df,
        pd.DataFrame,
    ):
        raise TypeError(
            f"{name} deve ser pandas DataFrame."
        )

    if df.empty:
        raise ValueError(
            f"{name} está vazio."
        )


def _latest_by_ticker(
    df: pd.DataFrame,
) -> pd.DataFrame:
    """
    Garante somente o registro mais recente por ticker
    quando existir coluna date.
    """

    result = df.copy()

    result["ticker"] = (
        result["ticker"]
        .map(
            _normalize_ticker
        )
    )

    if "date" in result.columns:

        result["date"] = pd.to_datetime(
            result["date"],
            errors="coerce",
        )

        result = (
            result
            .sort_values(
                [
                    "ticker",
                    "date",
                ]
            )
            .groupby(
                "ticker",
                as_index=False,
            )
            .tail(1)
        )

    else:

        result = (
            result
            .drop_duplicates(
                subset=[
                    "ticker",
                ],
                keep="last",
            )
        )

    return (
        result
        .reset_index(
            drop=True
        )
    )


# ============================================================
# VALIDAÇÃO DA SELEÇÃO FUNDAMENTAL
# ============================================================

def validate_fundamental_selection(
    fundamental_selection: pd.DataFrame,
) -> bool:
    """
    Garante que somente empresas fundamentalmente
    selecionadas entrem no Portfolio Engine.
    """

    _validate_dataframe(
        fundamental_selection,
        "fundamental_selection",
    )

    required = {
        "ticker",
        "ranking_theme",
        "fundamental_position",
        "fundamental_factor",
        "fundamental_score",
        "selected_fundamentally",
    }

    missing = (
        required
        - set(
            fundamental_selection.columns
        )
    )

    if missing:

        raise KeyError(
            "Seleção fundamental sem colunas: "
            f"{sorted(missing)}"
        )

    if (
        ~fundamental_selection[
            "selected_fundamentally"
        ]
        .fillna(False)
        .astype(bool)
    ).any():

        raise AssertionError(
            "Portfolio Engine recebeu empresa "
            "não selecionada fundamentalmente."
        )

    themes = set(
        fundamental_selection[
            "ranking_theme"
        ]
        .astype(str)
        .str.upper()
    )

    invalid_themes = (
        themes
        - {
            ROBOTICS_THEME,
            QUANTUM_THEME,
        }
    )

    if invalid_themes:

        raise AssertionError(
            "Tema inválido no portfólio: "
            f"{sorted(invalid_themes)}"
        )

    robotics = (
        fundamental_selection.loc[
            fundamental_selection[
                "ranking_theme"
            ]
            .astype(str)
            .str.upper()
            ==
            ROBOTICS_THEME
        ]
    )

    quantum = (
        fundamental_selection.loc[
            fundamental_selection[
                "ranking_theme"
            ]
            .astype(str)
            .str.upper()
            ==
            QUANTUM_THEME
        ]
    )

    if len(robotics) > ROBOTICS_TOP_N:

        raise AssertionError(
            "Robotics excedeu Top 5."
        )

    if len(quantum) > QUANTUM_TOP_N:

        raise AssertionError(
            "Quantum excedeu Top 2."
        )

    if (
        not robotics.empty
        and
        (
            robotics[
                "fundamental_factor"
            ]
            .astype(str)
            .str.upper()
            !=
            "FINANCIAL_STRENGTH"
        ).any()
    ):

        raise AssertionError(
            "Robotics não está usando "
            "Financial Strength."
        )

    if (
        not quantum.empty
        and
        (
            quantum[
                "fundamental_factor"
            ]
            .astype(str)
            .str.upper()
            !=
            "GROWTH"
        ).any()
    ):

        raise AssertionError(
            "Quantum não está usando Growth."
        )

    return True


# ============================================================
# ROBOTICS
# ============================================================

def build_robotics_portfolio(
    robotics_selection: pd.DataFrame,
    signal_data: pd.DataFrame,
) -> pd.DataFrame:
    """
    Une o Top 5 fundamental Robotics ao resultado
    do Signal Engine.

    LEFT JOIN é obrigatório.

    Isso garante que uma empresa fundamentalmente
    selecionada continue selecionada mesmo quando
    o timing não estiver aprovado.
    """

    _validate_dataframe(
        robotics_selection,
        "robotics_selection",
    )

    _validate_dataframe(
        signal_data,
        "signal_data",
    )

    if "ticker" not in signal_data.columns:

        raise KeyError(
            "Signal Engine sem coluna ticker."
        )

    fundamental = (
        robotics_selection.copy()
    )

    fundamental["ticker"] = (
        fundamental["ticker"]
        .map(
            _normalize_ticker
        )
    )

    signals = (
        _latest_by_ticker(
            signal_data
        )
    )

    # --------------------------------------------------------
    # EVITAR COLISÃO COM COLUNAS FUNDAMENTAIS
    # --------------------------------------------------------

    protected_columns = set(
        fundamental.columns
    )

    protected_columns.discard(
        "ticker"
    )

    rename_map = {}

    for column in signals.columns:

        if (
            column != "ticker"
            and
            column in protected_columns
        ):

            rename_map[column] = (
                f"timing_{column}"
            )

    if rename_map:

        signals = signals.rename(
            columns=rename_map
        )

    # --------------------------------------------------------
    # LEFT JOIN
    # --------------------------------------------------------

    result = fundamental.merge(
        signals,
        on="ticker",
        how="left",
        validate="one_to_one",
    )

    # --------------------------------------------------------
    # POLÍTICA
    # --------------------------------------------------------

    result[
        "timing_engine"
    ] = (
        "AI_INFRASTRUCTURE_SIGNAL_ENGINE"
    )

    result[
        "timing_used_for_entry"
    ] = True

    result[
        "timing_used_for_contribution"
    ] = True

    result[
        "timing_changes_ownership"
    ] = False

    result[
        "timing_generates_sell"
    ] = False

    result[
        "timing_changes_fundamental_rank"
    ] = False

    result[
        "ownership_source"
    ] = (
        "FUNDAMENTAL_SELECTION"
    )

    # --------------------------------------------------------
    # SINAL ORIGINAL
    # --------------------------------------------------------

    if "signal_approved" in result.columns:

        approved = (
            result[
                "signal_approved"
            ]
            .fillna(False)
            .astype(bool)
        )

        signal_available = (
            result[
                "signal_approved"
            ]
            .notna()
        )

    else:

        approved = pd.Series(
            False,
            index=result.index,
            dtype=bool,
        )

        signal_available = pd.Series(
            False,
            index=result.index,
            dtype=bool,
        )

    result[
        "entry_timing_approved"
    ] = approved

    # --------------------------------------------------------
    # DECISÃO OPERACIONAL
    # --------------------------------------------------------

    result[
        "entry_action"
    ] = np.where(
        ~signal_available,
        "TIMING INDISPONÍVEL",
        np.where(
            approved,
            "ENTRADA/APORTE AUTORIZADO",
            "AGUARDAR TIMING",
        ),
    )

    # A empresa continua selecionada independentemente
    # do timing.

    result[
        "portfolio_selected"
    ] = True

    result[
        "selection_reason"
    ] = (
        "ROBOTICS_TOP5_FINANCIAL_STRENGTH"
    )

    # --------------------------------------------------------
    # PROTEÇÃO
    # --------------------------------------------------------

    if len(result) != len(
        fundamental
    ):

        raise AssertionError(
            "Timing alterou a quantidade de "
            "empresas Robotics."
        )

    if set(
        result["ticker"]
    ) != set(
        fundamental["ticker"]
    ):

        raise AssertionError(
            "Timing alterou a composição "
            "fundamental Robotics."
        )

    original_rank = (
        fundamental[
            [
                "ticker",
                "fundamental_position",
            ]
        ]
        .set_index(
            "ticker"
        )[
            "fundamental_position"
        ]
        .to_dict()
    )

    final_rank = (
        result[
            [
                "ticker",
                "fundamental_position",
            ]
        ]
        .set_index(
            "ticker"
        )[
            "fundamental_position"
        ]
        .to_dict()
    )

    if original_rank != final_rank:

        raise AssertionError(
            "Timing alterou ranking fundamental "
            "Robotics."
        )

    return result


# ============================================================
# QUANTUM
# ============================================================

def build_quantum_portfolio(
    quantum_selection: pd.DataFrame,
) -> pd.DataFrame:
    """
    Quantum utiliza somente Growth Top 2.

    Não recebe Institutional Score,
    Technical Score, Entry Timing ou Signal Engine.
    """

    _validate_dataframe(
        quantum_selection,
        "quantum_selection",
    )

    result = (
        quantum_selection.copy()
    )

    result["ticker"] = (
        result["ticker"]
        .map(
            _normalize_ticker
        )
    )

    result[
        "timing_engine"
    ] = "NONE"

    result[
        "timing_used_for_entry"
    ] = False

    result[
        "timing_used_for_contribution"
    ] = False

    result[
        "timing_changes_ownership"
    ] = False

    result[
        "timing_generates_sell"
    ] = False

    result[
        "timing_changes_fundamental_rank"
    ] = False

    result[
        "entry_timing_approved"
    ] = pd.NA

    result[
        "entry_action"
    ] = (
        "ENTRADA FUNDAMENTAL"
    )

    result[
        "portfolio_selected"
    ] = True

    result[
        "ownership_source"
    ] = (
        "FUNDAMENTAL_SELECTION"
    )

    result[
        "selection_reason"
    ] = (
        "QUANTUM_TOP2_GROWTH"
    )

    return result


# ============================================================
# CONSOLIDAÇÃO
# ============================================================

def consolidate_portfolio(
    robotics: pd.DataFrame,
    quantum: pd.DataFrame,
) -> pd.DataFrame:
    """
    Consolida as duas estratégias.

    Empresas BOTH podem ter duas teses independentes.

    Exemplo:
        NVDA / ROBOTICS
        NVDA / QUANTUM

    Não deduplicamos essas teses neste estágio.
    """

    frames = []

    if (
        robotics is not None
        and
        not robotics.empty
    ):

        frames.append(
            robotics.copy()
        )

    if (
        quantum is not None
        and
        not quantum.empty
    ):

        frames.append(
            quantum.copy()
        )

    if not frames:

        raise RuntimeError(
            "Portfólio final vazio."
        )

    result = pd.concat(
        frames,
        ignore_index=True,
        sort=False,
    )

    result[
        "ranking_theme"
    ] = (
        result[
            "ranking_theme"
        ]
        .astype(str)
        .str.upper()
    )

    theme_order = pd.Categorical(
        result[
            "ranking_theme"
        ],
        categories=[
            ROBOTICS_THEME,
            QUANTUM_THEME,
        ],
        ordered=True,
    )

    result = (
        result
        .assign(
            _theme_order=theme_order
        )
        .sort_values(
            [
                "_theme_order",
                "fundamental_position",
                "ticker",
            ]
        )
        .drop(
            columns=[
                "_theme_order",
            ]
        )
        .reset_index(
            drop=True
        )
    )

    return result


# ============================================================
# PORTFÓLIO ÚNICO POR EMPRESA
# ============================================================

def build_unique_company_view(
    portfolio: pd.DataFrame,
) -> pd.DataFrame:
    """
    Cria visão auxiliar de empresas únicas.

    IMPORTANTE:
    Isto NÃO elimina a dupla tese de uma empresa BOTH
    do resultado oficial.

    Serve apenas para responder:
    "quantas empresas diferentes foram selecionadas?"
    """

    _validate_dataframe(
        portfolio,
        "portfolio",
    )

    rows = []

    for ticker, group in portfolio.groupby(
        "ticker",
        sort=True,
    ):

        themes = sorted(
            set(
                group[
                    "ranking_theme"
                ]
                .astype(str)
                .str.upper()
            )
        )

        actions = sorted(
            set(
                group[
                    "entry_action"
                ]
                .dropna()
                .astype(str)
            )
        )

        rows.append(
            {
                "ticker":
                    ticker,

                "themes":
                    " + ".join(
                        themes
                    ),

                "number_of_theses":
                    len(group),

                "entry_actions":
                    " | ".join(
                        actions
                    ),

                "selected":
                    True,
            }
        )

    return pd.DataFrame(
        rows
    )


# ============================================================
# MOTOR PRINCIPAL
# ============================================================

class PortfolioEngine:
    """
    Integra seleção fundamental e timing.

    Não recalcula fundamentos.
    Não recalcula Signal Engine.
    """

    def __init__(self) -> None:

        self.robotics = (
            pd.DataFrame()
        )

        self.quantum = (
            pd.DataFrame()
        )

        self.portfolio = (
            pd.DataFrame()
        )

        self.unique_companies = (
            pd.DataFrame()
        )

    def calculate(
        self,
        fundamental_selection: pd.DataFrame,
        robotics_signal_data: pd.DataFrame,
    ) -> pd.DataFrame:
        """
        Gera o portfólio final.
        """

        validate_fundamental_selection(
            fundamental_selection
        )

        selection = (
            fundamental_selection
            .copy()
        )

        selection[
            "ranking_theme"
        ] = (
            selection[
                "ranking_theme"
            ]
            .astype(str)
            .str.upper()
        )

        robotics_selection = (
            selection.loc[
                selection[
                    "ranking_theme"
                ]
                ==
                ROBOTICS_THEME
            ]
            .copy()
        )

        quantum_selection = (
            selection.loc[
                selection[
                    "ranking_theme"
                ]
                ==
                QUANTUM_THEME
            ]
            .copy()
        )

        if robotics_selection.empty:

            raise RuntimeError(
                "Top 5 Robotics vazio."
            )

        if quantum_selection.empty:

            raise RuntimeError(
                "Top 2 Quantum vazio."
            )

        self.robotics = (
            build_robotics_portfolio(
                robotics_selection=
                    robotics_selection,

                signal_data=
                    robotics_signal_data,
            )
        )

        self.quantum = (
            build_quantum_portfolio(
                quantum_selection
            )
        )

        self.portfolio = (
            consolidate_portfolio(
                robotics=
                    self.robotics,

                quantum=
                    self.quantum,
            )
        )

        self.unique_companies = (
            build_unique_company_view(
                self.portfolio
            )
        )

        self.validate()

        self.print_summary()

        return (
            self.portfolio.copy()
        )

    def validate(self) -> bool:
        """
        Auditoria final da arquitetura congelada.
        """

        if self.portfolio.empty:

            raise AssertionError(
                "Portfólio final vazio."
            )

        robotics = (
            self.portfolio.loc[
                self.portfolio[
                    "ranking_theme"
                ]
                ==
                ROBOTICS_THEME
            ]
        )

        quantum = (
            self.portfolio.loc[
                self.portfolio[
                    "ranking_theme"
                ]
                ==
                QUANTUM_THEME
            ]
        )

        if len(robotics) > 5:

            raise AssertionError(
                "Robotics excedeu Top 5."
            )

        if len(quantum) > 2:

            raise AssertionError(
                "Quantum excedeu Top 2."
            )

        if (
            robotics[
                "timing_changes_ownership"
            ]
            .fillna(False)
            .astype(bool)
            .any()
        ):

            raise AssertionError(
                "Timing está alterando ownership."
            )

        if (
            robotics[
                "timing_generates_sell"
            ]
            .fillna(False)
            .astype(bool)
            .any()
        ):

            raise AssertionError(
                "Timing está gerando venda."
            )

        if (
            robotics[
                "timing_changes_fundamental_rank"
            ]
            .fillna(False)
            .astype(bool)
            .any()
        ):

            raise AssertionError(
                "Timing alterou ranking fundamental."
            )

        if (
            quantum[
                "timing_engine"
            ]
            .astype(str)
            .str.upper()
            !=
            "NONE"
        ).any():

            raise AssertionError(
                "Timing foi aplicado a Quantum."
            )

        if (
            ~self.portfolio[
                "portfolio_selected"
            ]
            .fillna(False)
            .astype(bool)
        ).any():

            raise AssertionError(
                "Empresa fundamentalmente selecionada "
                "foi removida pelo Portfolio Engine."
            )

        return True

    def get_robotics(
        self,
    ) -> pd.DataFrame:

        return (
            self.robotics.copy()
        )

    def get_quantum(
        self,
    ) -> pd.DataFrame:

        return (
            self.quantum.copy()
        )

    def get_portfolio(
        self,
    ) -> pd.DataFrame:

        return (
            self.portfolio.copy()
        )

    def get_unique_companies(
        self,
    ) -> pd.DataFrame:

        return (
            self.unique_companies.copy()
        )

    def print_summary(
        self,
    ) -> None:
        """
        Resumo operacional.
        """

        print()
        print(
            "=" * 100
        )

        print(
            "ROBOTICS_QUANTUM_SP500 — "
            "PORTFOLIO ENGINE"
        )

        print(
            "=" * 100
        )

        print(
            "\nROBOTICS"
        )

        print(
            f"Selecionadas fundamentalmente: "
            f"{len(self.robotics)}"
        )

        if (
            "entry_timing_approved"
            in self.robotics.columns
        ):

            approved = int(
                self.robotics[
                    "entry_timing_approved"
                ]
                .fillna(False)
                .astype(bool)
                .sum()
            )

            print(
                "Timing aprovado para "
                f"entrada/aporte: {approved}"
            )

        print(
            "\nQUANTUM"
        )

        print(
            "Selecionadas fundamentalmente: "
            f"{len(self.quantum)}"
        )

        print(
            "Timing técnico: NÃO UTILIZADO"
        )

        print(
            "\nPORTFÓLIO"
        )

        print(
            "Teses selecionadas: "
            f"{len(self.portfolio)}"
        )

        print(
            "Empresas únicas: "
            f"{len(self.unique_companies)}"
        )

        display_columns = [
            "ranking_theme",
            "fundamental_position",
            "ticker",
            "company",
            "fundamental_factor",
            "fundamental_score",
            "entry_action",
        ]

        available = [
            column
            for column in display_columns
            if column
            in self.portfolio.columns
        ]

        print()

        print(
            self.portfolio[
                available
            ]
            .to_string(
                index=False
            )
        )

        print(
            "=" * 100
        )


# ============================================================
# INTERFACE SIMPLIFICADA
# ============================================================

def build_portfolio(
    fundamental_selection: pd.DataFrame,
    robotics_signal_data: pd.DataFrame,
) -> pd.DataFrame:
    """
    Interface simplificada.
    """

    engine = (
        PortfolioEngine()
    )

    return engine.calculate(
        fundamental_selection=
            fundamental_selection,

        robotics_signal_data=
            robotics_signal_data,
    )
