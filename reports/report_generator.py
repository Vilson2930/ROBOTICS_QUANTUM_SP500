# ======================================================================================
# ROBOTICS_QUANTUM_SP500
# reports/report_generator.py
# ======================================================================================
#
# RESPONSABILIDADE
# ---------------
# Gerar os relatórios finais do robô.
#
# ARQUITETURA CONGELADA
# ---------------------
#
# ROBOTICS
#   -> Financial Strength
#   -> Top 5
#   -> AI Infrastructure Signal Engine
#   -> timing SOMENTE para entrada/aporte
#
# QUANTUM
#   -> Growth
#   -> Top 2
#   -> SEM timing
#
# PRINCÍPIOS
# ----------
# • Timing não altera seleção fundamental.
# • Timing não altera ranking fundamental.
# • Timing não gera venda.
# • QUANTUM não recebe decisão do timing engine.
#
# ARQUIVOS GERADOS
# ----------------
# outputs/
#   portfolio_final.csv
#   robotics_selection.csv
#   quantum_selection.csv
#   executive_summary.txt
#
# ======================================================================================

from __future__ import annotations

from pathlib import Path
from typing import Dict

import numpy as np
import pandas as pd

from config.settings import OUTPUTS_DIR


# ======================================================================================
# 1. DIRETÓRIOS
# ======================================================================================

OUTPUT_PATH = Path(
    OUTPUTS_DIR
)

OUTPUT_PATH.mkdir(
    parents=True,
    exist_ok=True,
)

PORTFOLIO_FILE = (
    OUTPUT_PATH
    /
    "portfolio_final.csv"
)

ROBOTICS_FILE = (
    OUTPUT_PATH
    /
    "robotics_selection.csv"
)

QUANTUM_FILE = (
    OUTPUT_PATH
    /
    "quantum_selection.csv"
)

EXECUTIVE_SUMMARY_FILE = (
    OUTPUT_PATH
    /
    "executive_summary.txt"
)


# ======================================================================================
# 2. CONSTANTES
# ======================================================================================

ROBOTICS_THEME = "ROBOTICS"
QUANTUM_THEME = "QUANTUM"

ROBOTICS_TOP_N = 5
QUANTUM_TOP_N = 2


# ======================================================================================
# 3. HELPERS
# ======================================================================================

def _normalize_boolean(
    value,
) -> bool:

    if isinstance(
        value,
        (bool, np.bool_),
    ):
        return bool(value)

    if pd.isna(value):
        return False

    text = (
        str(value)
        .strip()
        .upper()
    )

    return text in {
        "TRUE",
        "1",
        "YES",
        "SIM",
        "Y",
        "S",
    }


def _safe_value(
    row,
    column: str,
    default="",
):

    if column not in row.index:
        return default

    value = row[column]

    if pd.isna(value):
        return default

    return value


def _format_score(
    value,
) -> str:

    try:

        value = float(value)

        if not np.isfinite(value):
            return "-"

        return f"{value:.4f}"

    except Exception:

        return "-"


def _format_price(
    value,
) -> str:

    try:

        value = float(value)

        if not np.isfinite(value):
            return "-"

        return f"{value:.2f}"

    except Exception:

        return "-"


# ======================================================================================
# 4. VALIDAÇÃO DO PORTFÓLIO
# ======================================================================================

def validate_portfolio_report(
    portfolio: pd.DataFrame,
) -> None:

    if portfolio is None:
        raise RuntimeError(
            "Portfolio final inexistente."
        )

    if portfolio.empty:
        raise RuntimeError(
            "Portfolio final vazio."
        )

    required_columns = {
        "ticker",
        "ranking_theme",
        "fundamental_position",
        "fundamental_factor",
        "fundamental_score",
        "portfolio_selected",
        "entry_action",
    }

    missing = (
        required_columns
        -
        set(
            portfolio.columns
        )
    )

    if missing:

        raise RuntimeError(
            "Portfolio final sem colunas "
            f"obrigatórias: {sorted(missing)}"
        )

    robotics = portfolio[
        portfolio[
            "ranking_theme"
        ]
        ==
        ROBOTICS_THEME
    ].copy()

    quantum = portfolio[
        portfolio[
            "ranking_theme"
        ]
        ==
        QUANTUM_THEME
    ].copy()

    if len(robotics) != ROBOTICS_TOP_N:

        raise RuntimeError(
            "Relatório recebeu quantidade "
            "incorreta de ROBOTICS: "
            f"{len(robotics)}. "
            f"Esperado: {ROBOTICS_TOP_N}."
        )

    if len(quantum) != QUANTUM_TOP_N:

        raise RuntimeError(
            "Relatório recebeu quantidade "
            "incorreta de QUANTUM: "
            f"{len(quantum)}. "
            f"Esperado: {QUANTUM_TOP_N}."
        )

    if not (
        robotics[
            "fundamental_factor"
        ]
        ==
        "financial_strength"
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
        "growth"
    ).all():

        raise RuntimeError(
            "QUANTUM não está utilizando "
            "Growth."
        )

    if not (
        portfolio[
            "portfolio_selected"
        ]
        .map(
            _normalize_boolean
        )
        .all()
    ):

        raise RuntimeError(
            "Portfolio final contém empresa "
            "fora da seleção fundamental."
        )


# ======================================================================================
# 5. SEPARAÇÃO DOS TEMAS
# ======================================================================================

def split_portfolio(
    portfolio: pd.DataFrame,
):

    robotics = (
        portfolio[
            portfolio[
                "ranking_theme"
            ]
            ==
            ROBOTICS_THEME
        ]
        .copy()
        .sort_values(
            "fundamental_position"
        )
        .reset_index(
            drop=True
        )
    )

    quantum = (
        portfolio[
            portfolio[
                "ranking_theme"
            ]
            ==
            QUANTUM_THEME
        ]
        .copy()
        .sort_values(
            "fundamental_position"
        )
        .reset_index(
            drop=True
        )
    )

    return (
        robotics,
        quantum,
    )


# ======================================================================================
# 6. VIEW ROBOTICS
# ======================================================================================

def build_robotics_report(
    robotics: pd.DataFrame,
) -> pd.DataFrame:

    if robotics.empty:
        return pd.DataFrame()

    report = pd.DataFrame()

    report[
        "position"
    ] = robotics[
        "fundamental_position"
    ].astype(int)

    report[
        "ticker"
    ] = robotics[
        "ticker"
    ]

    if "security" in robotics.columns:

        report[
            "company"
        ] = robotics[
            "security"
        ]

    elif "company" in robotics.columns:

        report[
            "company"
        ] = robotics[
            "company"
        ]

    else:

        report[
            "company"
        ] = ""

    report[
        "theme"
    ] = ROBOTICS_THEME

    report[
        "fundamental_factor"
    ] = robotics[
        "fundamental_factor"
    ]

    report[
        "fundamental_score"
    ] = robotics[
        "fundamental_score"
    ]

    # ------------------------------------------------------------------
    # SIGNAL ENGINE
    # ------------------------------------------------------------------

    if "final_score" in robotics.columns:

        report[
            "signal_score"
        ] = robotics[
            "final_score"
        ]

    else:

        report[
            "signal_score"
        ] = np.nan

    if "signal_status" in robotics.columns:

        report[
            "signal_status"
        ] = robotics[
            "signal_status"
        ]

    else:

        report[
            "signal_status"
        ] = ""

    if "signal_approved" in robotics.columns:

        report[
            "signal_approved"
        ] = robotics[
            "signal_approved"
        ].map(
            _normalize_boolean
        )

    else:

        report[
            "signal_approved"
        ] = False

    # ------------------------------------------------------------------
    # ENTRY TIMING ENGINE
    #
    # IMPORTANTE:
    # o nome oficial produzido pelo engine é:
    #
    #       timing_approved
    #
    # e NÃO:
    #
    #       entry_timing_approved
    # ------------------------------------------------------------------

    if "entry_timing_score" in robotics.columns:

        report[
            "entry_timing_score"
        ] = robotics[
            "entry_timing_score"
        ]

    else:

        report[
            "entry_timing_score"
        ] = np.nan

    if "timing_status" in robotics.columns:

        report[
            "timing_status"
        ] = robotics[
            "timing_status"
        ]

    else:

        report[
            "timing_status"
        ] = ""

    if "timing_approved" in robotics.columns:

        report[
            "timing_approved"
        ] = robotics[
            "timing_approved"
        ].map(
            _normalize_boolean
        )

    else:

        report[
            "timing_approved"
        ] = False

    # ------------------------------------------------------------------
    # AÇÃO
    # ------------------------------------------------------------------

    report[
        "entry_action"
    ] = robotics[
        "entry_action"
    ]

    # ------------------------------------------------------------------
    # PREÇO
    # ------------------------------------------------------------------

    price_candidates = [
        "close",
        "price",
        "current_price",
    ]

    price_column = None

    for candidate in price_candidates:

        if candidate in robotics.columns:

            price_column = candidate
            break

    if price_column is not None:

        report[
            "price"
        ] = robotics[
            price_column
        ]

    else:

        report[
            "price"
        ] = np.nan

    # ------------------------------------------------------------------
    # AUDITORIA DA ARQUITETURA
    # ------------------------------------------------------------------

    report[
        "timing_engine"
    ] = (
        "AI_INFRASTRUCTURE_SIGNAL_ENGINE"
    )

    report[
        "timing_changes_ownership"
    ] = False

    report[
        "timing_generates_sell"
    ] = False

    report[
        "timing_changes_fundamental_rank"
    ] = False

    return report


# ======================================================================================
# 7. VIEW QUANTUM
# ======================================================================================

def build_quantum_report(
    quantum: pd.DataFrame,
) -> pd.DataFrame:

    if quantum.empty:
        return pd.DataFrame()

    report = pd.DataFrame()

    report[
        "position"
    ] = quantum[
        "fundamental_position"
    ].astype(int)

    report[
        "ticker"
    ] = quantum[
        "ticker"
    ]

    if "security" in quantum.columns:

        report[
            "company"
        ] = quantum[
            "security"
        ]

    elif "company" in quantum.columns:

        report[
            "company"
        ] = quantum[
            "company"
        ]

    else:

        report[
            "company"
        ] = ""

    report[
        "theme"
    ] = QUANTUM_THEME

    report[
        "fundamental_factor"
    ] = quantum[
        "fundamental_factor"
    ]

    report[
        "fundamental_score"
    ] = quantum[
        "fundamental_score"
    ]

    # QUANTUM NÃO USA TIMING

    report[
        "signal_score"
    ] = np.nan

    report[
        "signal_status"
    ] = "NÃO UTILIZADO"

    report[
        "signal_approved"
    ] = False

    report[
        "entry_timing_score"
    ] = np.nan

    report[
        "timing_status"
    ] = "NÃO UTILIZADO"

    report[
        "timing_approved"
    ] = False

    report[
        "entry_action"
    ] = quantum[
        "entry_action"
    ]

    report[
        "price"
    ] = np.nan

    report[
        "timing_engine"
    ] = "NONE"

    report[
        "timing_changes_ownership"
    ] = False

    report[
        "timing_generates_sell"
    ] = False

    report[
        "timing_changes_fundamental_rank"
    ] = False

    return report


# ======================================================================================
# 8. RESUMO EXECUTIVO
# ======================================================================================

def build_executive_summary(
    portfolio: pd.DataFrame,
) -> str:

    robotics, quantum = (
        split_portfolio(
            portfolio
        )
    )

    lines = []

    lines.append(
        "=" * 90
    )

    lines.append(
        "ROBOTICS_QUANTUM_SP500"
    )

    lines.append(
        "RELATÓRIO EXECUTIVO"
    )

    lines.append(
        "=" * 90
    )

    lines.append("")

    lines.append(
        "ARQUITETURA"
    )

    lines.append(
        "-----------"
    )

    lines.append(
        "ROBOTICS:"
    )

    lines.append(
        "  Financial Strength -> Top 5"
    )

    lines.append(
        "  Timing: AI Infrastructure Signal Engine"
    )

    lines.append(
        "  Timing utilizado somente para entrada/aporte."
    )

    lines.append("")

    lines.append(
        "QUANTUM:"
    )

    lines.append(
        "  Growth -> Top 2"
    )

    lines.append(
        "  Timing: NÃO UTILIZADO"
    )

    lines.append("")

    lines.append(
        "REGRAS DE SEGURANÇA:"
    )

    lines.append(
        "  Timing não altera propriedade."
    )

    lines.append(
        "  Timing não altera ranking fundamental."
    )

    lines.append(
        "  Timing não gera venda."
    )

    lines.append("")

    # ------------------------------------------------------------------
    # ROBOTICS
    # ------------------------------------------------------------------

    lines.append(
        "=" * 90
    )

    lines.append(
        "ROBOTICS — TOP 5"
    )

    lines.append(
        "=" * 90
    )

    for row in robotics.itertuples(
        index=False
    ):

        ticker = getattr(
            row,
            "ticker",
            "",
        )

        position = getattr(
            row,
            "fundamental_position",
            "",
        )

        fundamental_score = getattr(
            row,
            "fundamental_score",
            np.nan,
        )

        final_score = getattr(
            row,
            "final_score",
            np.nan,
        )

        signal_status = getattr(
            row,
            "signal_status",
            "",
        )

        timing_status = getattr(
            row,
            "timing_status",
            "",
        )

        timing_approved = (
            _normalize_boolean(
                getattr(
                    row,
                    "timing_approved",
                    False,
                )
            )
        )

        signal_approved = (
            _normalize_boolean(
                getattr(
                    row,
                    "signal_approved",
                    False,
                )
            )
        )

        entry_action = getattr(
            row,
            "entry_action",
            "",
        )

        lines.append(
            f"{position}. {ticker}"
        )

        lines.append(
            "   Fundamental Score: "
            f"{_format_score(fundamental_score)}"
        )

        lines.append(
            "   Signal Score: "
            f"{_format_score(final_score)}"
        )

        lines.append(
            "   Signal Status: "
            f"{signal_status}"
        )

        lines.append(
            "   Timing Status: "
            f"{timing_status}"
        )

        lines.append(
            "   Timing Approved: "
            f"{timing_approved}"
        )

        lines.append(
            "   Signal Approved: "
            f"{signal_approved}"
        )

        lines.append(
            "   Ação: "
            f"{entry_action}"
        )

        lines.append("")

    # ------------------------------------------------------------------
    # QUANTUM
    # ------------------------------------------------------------------

    lines.append(
        "=" * 90
    )

    lines.append(
        "QUANTUM — TOP 2"
    )

    lines.append(
        "=" * 90
    )

    for row in quantum.itertuples(
        index=False
    ):

        ticker = getattr(
            row,
            "ticker",
            "",
        )

        position = getattr(
            row,
            "fundamental_position",
            "",
        )

        fundamental_score = getattr(
            row,
            "fundamental_score",
            np.nan,
        )

        entry_action = getattr(
            row,
            "entry_action",
            "",
        )

        lines.append(
            f"{position}. {ticker}"
        )

        lines.append(
            "   Fundamental Score: "
            f"{_format_score(fundamental_score)}"
        )

        lines.append(
            "   Timing: NÃO UTILIZADO"
        )

        lines.append(
            "   Ação: "
            f"{entry_action}"
        )

        lines.append("")

    return "\n".join(
        lines
    )


# ======================================================================================
# 9. SALVAR RELATÓRIOS
# ======================================================================================

def save_reports(
    portfolio: pd.DataFrame,
) -> Dict[str, Path]:

    validate_portfolio_report(
        portfolio
    )

    robotics, quantum = (
        split_portfolio(
            portfolio
        )
    )

    robotics_report = (
        build_robotics_report(
            robotics
        )
    )

    quantum_report = (
        build_quantum_report(
            quantum
        )
    )

    executive_summary = (
        build_executive_summary(
            portfolio
        )
    )

    OUTPUT_PATH.mkdir(
        parents=True,
        exist_ok=True,
    )

    portfolio.to_csv(
        PORTFOLIO_FILE,
        index=False,
    )

    robotics_report.to_csv(
        ROBOTICS_FILE,
        index=False,
    )

    quantum_report.to_csv(
        QUANTUM_FILE,
        index=False,
    )

    EXECUTIVE_SUMMARY_FILE.write_text(
        executive_summary,
        encoding="utf-8",
    )

    return {
        "portfolio":
            PORTFOLIO_FILE,

        "robotics":
            ROBOTICS_FILE,

        "quantum":
            QUANTUM_FILE,

        "executive_summary":
            EXECUTIVE_SUMMARY_FILE,
    }


# ======================================================================================
# 10. FACHADA
# ======================================================================================

class ReportGenerator:

    @staticmethod
    def generate(
        portfolio: pd.DataFrame,
    ) -> Dict[str, Path]:

        return save_reports(
            portfolio
        )


# ======================================================================================
# 11. TESTE DIRETO
# ======================================================================================

if __name__ == "__main__":

    print(
        "=" * 100
    )

    print(
        "ROBOTICS_QUANTUM_SP500 "
        "— REPORT GENERATOR"
    )

    print(
        "=" * 100
    )

    print("")

    print(
        "Relatórios:"
    )

    print(
        f"  {PORTFOLIO_FILE}"
    )

    print(
        f"  {ROBOTICS_FILE}"
    )

    print(
        f"  {QUANTUM_FILE}"
    )

    print(
        f"  {EXECUTIVE_SUMMARY_FILE}"
    )

    print("")

    print(
        "Arquitetura:"
    )

    print(
        "  ROBOTICS = "
        "Financial Strength Top 5 "
        "+ AI Infrastructure Signal Engine"
    )

    print(
        "  QUANTUM = "
        "Growth Top 2 "
        "+ sem timing"
    )

    print("")

    print(
        "Report Generator carregado "
        "com sucesso."
    )
