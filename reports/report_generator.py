"""
ROBOTICS_QUANTUM_SP500
======================

Gerador do relatório operacional final.

O relatório apresenta separadamente:

ROBOTICS
    Financial Strength -> Top 5
    +
    AI Infrastructure Signal Engine
    apenas para timing de entrada/aporte.

QUANTUM
    Growth -> Top 2
    +
    sem timing técnico.

Este módulo NÃO:
- recalcula fundamentos;
- recalcula timing;
- altera ranking;
- altera ownership;
- gera venda.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd


# ============================================================
# DIRETÓRIOS
# ============================================================

BASE_DIR = Path(__file__).resolve().parents[1]

REPORTS_DIR = (
    BASE_DIR
    / "outputs"
)

DEFAULT_CSV_FILE = (
    REPORTS_DIR
    / "portfolio_final.csv"
)

DEFAULT_ROBOTICS_FILE = (
    REPORTS_DIR
    / "robotics_selection.csv"
)

DEFAULT_QUANTUM_FILE = (
    REPORTS_DIR
    / "quantum_selection.csv"
)

DEFAULT_SUMMARY_FILE = (
    REPORTS_DIR
    / "executive_summary.txt"
)


# ============================================================
# AUXILIARES
# ============================================================

def _ensure_output_directory() -> None:
    """
    Garante existência da pasta de saída.
    """

    REPORTS_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )


def _safe_text(
    value,
    default: str = "-",
) -> str:
    """
    Converte valor em texto de forma segura.
    """

    if value is None:
        return default

    try:

        if pd.isna(value):
            return default

    except Exception:
        pass

    text = str(
        value
    ).strip()

    return (
        text
        if text
        else default
    )


def _safe_float(
    value,
) -> float:
    """
    Conversão numérica segura.
    """

    try:

        result = float(
            value
        )

        if np.isfinite(
            result
        ):
            return result

    except Exception:
        pass

    return np.nan


def _format_score(
    value,
) -> str:
    """
    Formata score fundamental/técnico.
    """

    number = _safe_float(
        value
    )

    if not np.isfinite(
        number
    ):
        return "-"

    # Fundamental score normalmente está
    # em escala 0-1.

    if (
        number >= 0
        and
        number <= 1
    ):
        return (
            f"{number * 100:.2f}"
        )

    return (
        f"{number:.2f}"
    )


def _format_date(
    value,
) -> str:
    """
    Formata data.
    """

    if value is None:
        return "-"

    try:

        date = pd.to_datetime(
            value,
            errors="coerce",
        )

        if pd.isna(
            date
        ):
            return "-"

        return date.strftime(
            "%Y-%m-%d"
        )

    except Exception:

        return "-"


def _first_existing_column(
    df: pd.DataFrame,
    candidates: list[str],
) -> Optional[str]:
    """
    Retorna a primeira coluna disponível.
    """

    for column in candidates:

        if column in df.columns:
            return column

    return None


# ============================================================
# VALIDAÇÃO
# ============================================================

def validate_portfolio_report_input(
    portfolio: pd.DataFrame,
) -> bool:
    """
    Valida entrada do relatório.
    """

    if not isinstance(
        portfolio,
        pd.DataFrame,
    ):
        raise TypeError(
            "portfolio deve ser pandas DataFrame."
        )

    if portfolio.empty:
        raise ValueError(
            "Portfólio final vazio."
        )

    required = {
        "ticker",
        "ranking_theme",
        "fundamental_position",
        "fundamental_factor",
        "fundamental_score",
        "portfolio_selected",
        "entry_action",
    }

    missing = (
        required
        - set(
            portfolio.columns
        )
    )

    if missing:

        raise KeyError(
            "Portfólio sem colunas obrigatórias: "
            f"{sorted(missing)}"
        )

    invalid_themes = (
        set(
            portfolio[
                "ranking_theme"
            ]
            .astype(str)
            .str.upper()
        )
        -
        {
            "ROBOTICS",
            "QUANTUM",
        }
    )

    if invalid_themes:

        raise AssertionError(
            "Temas inválidos no relatório: "
            f"{sorted(invalid_themes)}"
        )

    if (
        ~portfolio[
            "portfolio_selected"
        ]
        .fillna(False)
        .astype(bool)
    ).any():

        raise AssertionError(
            "Relatório recebeu empresa "
            "não selecionada."
        )

    return True


# ============================================================
# SEPARAÇÃO DOS MOTORES
# ============================================================

def split_portfolio(
    portfolio: pd.DataFrame,
) -> tuple[
    pd.DataFrame,
    pd.DataFrame,
]:
    """
    Separa Robotics e Quantum.
    """

    validate_portfolio_report_input(
        portfolio
    )

    df = portfolio.copy()

    df[
        "ranking_theme"
    ] = (
        df[
            "ranking_theme"
        ]
        .astype(str)
        .str.upper()
    )

    robotics = (
        df.loc[
            df[
                "ranking_theme"
            ]
            ==
            "ROBOTICS"
        ]
        .sort_values(
            [
                "fundamental_position",
                "ticker",
            ]
        )
        .reset_index(
            drop=True
        )
    )

    quantum = (
        df.loc[
            df[
                "ranking_theme"
            ]
            ==
            "QUANTUM"
        ]
        .sort_values(
            [
                "fundamental_position",
                "ticker",
            ]
        )
        .reset_index(
            drop=True
        )
    )

    if len(
        robotics
    ) > 5:

        raise AssertionError(
            "Relatório recebeu mais de "
            "5 empresas Robotics."
        )

    if len(
        quantum
    ) > 2:

        raise AssertionError(
            "Relatório recebeu mais de "
            "2 empresas Quantum."
        )

    return (
        robotics,
        quantum,
    )


# ============================================================
# VISÃO ROBOTICS
# ============================================================

def build_robotics_view(
    robotics: pd.DataFrame,
) -> pd.DataFrame:
    """
    Monta visão operacional Robotics.
    """

    if robotics.empty:
        return pd.DataFrame()

    output = pd.DataFrame(
        index=robotics.index
    )

    output[
        "POSIÇÃO"
    ] = robotics[
        "fundamental_position"
    ]

    output[
        "TICKER"
    ] = robotics[
        "ticker"
    ]

    if "company" in robotics.columns:

        output[
            "EMPRESA"
        ] = robotics[
            "company"
        ]

    else:

        output[
            "EMPRESA"
        ] = "-"

    if "exposure" in robotics.columns:

        output[
            "EXPOSIÇÃO"
        ] = robotics[
            "exposure"
        ]

    else:

        output[
            "EXPOSIÇÃO"
        ] = "-"

    output[
        "FATOR"
    ] = robotics[
        "fundamental_factor"
    ]

    output[
        "SCORE FUNDAMENTAL"
    ] = robotics[
        "fundamental_score"
    ].map(
        _format_score
    )

    # --------------------------------------------------------
    # SIGNAL ENGINE
    # --------------------------------------------------------

    signal_score_column = (
        _first_existing_column(
            robotics,
            [
                "signal_score",
                "combined_score",
                "final_score",
            ],
        )
    )

    if signal_score_column:

        output[
            "SIGNAL SCORE"
        ] = robotics[
            signal_score_column
        ].map(
            _format_score
        )

    else:

        output[
            "SIGNAL SCORE"
        ] = "-"

    # --------------------------------------------------------
    # TIMING STATUS
    # --------------------------------------------------------

    timing_status_column = (
        _first_existing_column(
            robotics,
            [
                "timing_status",
                "entry_timing_status",
            ],
        )
    )

    if timing_status_column:

        output[
            "TIMING"
        ] = robotics[
            timing_status_column
        ].map(
            _safe_text
        )

    else:

        output[
            "TIMING"
        ] = "-"

    # --------------------------------------------------------
    # DECISÃO FINAL DE ENTRADA
    # --------------------------------------------------------

    output[
        "AÇÃO"
    ] = robotics[
        "entry_action"
    ]

    if (
        "entry_timing_approved"
        in robotics.columns
    ):

        output[
            "TIMING APROVADO"
        ] = robotics[
            "entry_timing_approved"
        ].map(
            lambda value:
            "SIM"
            if bool(value)
            else "NÃO"
            if pd.notna(value)
            else "-"
        )

    else:

        output[
            "TIMING APROVADO"
        ] = "-"

    # --------------------------------------------------------
    # PREÇO
    # --------------------------------------------------------

    price_column = (
        _first_existing_column(
            robotics,
            [
                "close",
                "price",
                "current_price",
            ],
        )
    )

    if price_column:

        output[
            "PREÇO"
        ] = robotics[
            price_column
        ].map(
            lambda value:
            (
                f"{_safe_float(value):.2f}"
                if np.isfinite(
                    _safe_float(value)
                )
                else "-"
            )
        )

    else:

        output[
            "PREÇO"
        ] = "-"

    return output.reset_index(
        drop=True
    )


# ============================================================
# VISÃO QUANTUM
# ============================================================

def build_quantum_view(
    quantum: pd.DataFrame,
) -> pd.DataFrame:
    """
    Monta visão Quantum.

    Nenhum indicador técnico participa
    da decisão Quantum.
    """

    if quantum.empty:
        return pd.DataFrame()

    output = pd.DataFrame(
        index=quantum.index
    )

    output[
        "POSIÇÃO"
    ] = quantum[
        "fundamental_position"
    ]

    output[
        "TICKER"
    ] = quantum[
        "ticker"
    ]

    if "company" in quantum.columns:

        output[
            "EMPRESA"
        ] = quantum[
            "company"
        ]

    else:

        output[
            "EMPRESA"
        ] = "-"

    if "exposure" in quantum.columns:

        output[
            "EXPOSIÇÃO"
        ] = quantum[
            "exposure"
        ]

    else:

        output[
            "EXPOSIÇÃO"
        ] = "-"

    output[
        "FATOR"
    ] = quantum[
        "fundamental_factor"
    ]

    output[
        "SCORE FUNDAMENTAL"
    ] = quantum[
        "fundamental_score"
    ].map(
        _format_score
    )

    output[
        "TIMING"
    ] = (
        "NÃO UTILIZADO"
    )

    output[
        "AÇÃO"
    ] = quantum[
        "entry_action"
    ]

    return output.reset_index(
        drop=True
    )


# ============================================================
# RESUMO EXECUTIVO
# ============================================================

def build_executive_summary(
    portfolio: pd.DataFrame,
) -> str:
    """
    Produz resumo textual.
    """

    robotics, quantum = (
        split_portfolio(
            portfolio
        )
    )

    generated_at = (
        datetime.now(
            timezone.utc
        )
        .strftime(
            "%Y-%m-%d %H:%M UTC"
        )
    )

    lines = []

    lines.append(
        "=" * 100
    )

    lines.append(
        "ROBOTICS_QUANTUM_SP500"
    )

    lines.append(
        "RELATÓRIO OPERACIONAL"
    )

    lines.append(
        "=" * 100
    )

    lines.append(
        f"Gerado em: {generated_at}"
    )

    lines.append("")

    lines.append(
        "ARQUITETURA"
    )

    lines.append(
        "-" * 100
    )

    lines.append(
        "Universo: S&P 500"
    )

    lines.append(
        "Robotics: Financial Strength -> Top 5"
    )

    lines.append(
        "Robotics Timing: AI Infrastructure Signal Engine"
    )

    lines.append(
        "Quantum: Growth -> Top 2"
    )

    lines.append(
        "Quantum Timing: NÃO UTILIZADO"
    )

    lines.append(
        "Timing altera ownership: NÃO"
    )

    lines.append(
        "Timing gera venda: NÃO"
    )

    lines.append("")

    # --------------------------------------------------------
    # ROBOTICS
    # --------------------------------------------------------

    lines.append(
        "ROBOTICS"
    )

    lines.append(
        "-" * 100
    )

    lines.append(
        f"Selecionadas: {len(robotics)}"
    )

    if (
        "entry_timing_approved"
        in robotics.columns
    ):

        approved = int(
            robotics[
                "entry_timing_approved"
            ]
            .fillna(False)
            .astype(bool)
            .sum()
        )

    else:

        approved = 0

    lines.append(
        "Timing aprovado para entrada/aporte: "
        f"{approved}"
    )

    lines.append("")

    for _, row in robotics.iterrows():

        position = int(
            row[
                "fundamental_position"
            ]
        )

        ticker = _safe_text(
            row.get(
                "ticker"
            )
        )

        company = _safe_text(
            row.get(
                "company"
            )
        )

        score = _format_score(
            row.get(
                "fundamental_score"
            )
        )

        action = _safe_text(
            row.get(
                "entry_action"
            )
        )

        timing_status = "-"

        for candidate in [
            "timing_status",
            "entry_timing_status",
        ]:

            if candidate in row.index:

                timing_status = (
                    _safe_text(
                        row.get(
                            candidate
                        )
                    )
                )

                break

        lines.append(
            f"{position}. {ticker} — {company}"
        )

        lines.append(
            f"   Fundamental Score: {score}"
        )

        lines.append(
            f"   Timing: {timing_status}"
        )

        lines.append(
            f"   Ação: {action}"
        )

    lines.append("")

    # --------------------------------------------------------
    # QUANTUM
    # --------------------------------------------------------

    lines.append(
        "QUANTUM"
    )

    lines.append(
        "-" * 100
    )

    lines.append(
        f"Selecionadas: {len(quantum)}"
    )

    lines.append(
        "Timing técnico: NÃO UTILIZADO"
    )

    lines.append("")

    for _, row in quantum.iterrows():

        position = int(
            row[
                "fundamental_position"
            ]
        )

        ticker = _safe_text(
            row.get(
                "ticker"
            )
        )

        company = _safe_text(
            row.get(
                "company"
            )
        )

        score = _format_score(
            row.get(
                "fundamental_score"
            )
        )

        lines.append(
            f"{position}. {ticker} — {company}"
        )

        lines.append(
            f"   Growth Score: {score}"
        )

        lines.append(
            "   Entrada: FUNDAMENTAL"
        )

    lines.append("")

    # --------------------------------------------------------
    # AUDITORIA
    # --------------------------------------------------------

    lines.append(
        "AUDITORIA DE ARQUITETURA"
    )

    lines.append(
        "-" * 100
    )

    lines.append(
        "Robotics Fundamental: "
        "FINANCIAL_STRENGTH / TOP 5"
    )

    lines.append(
        "Quantum Fundamental: "
        "GROWTH / TOP 2"
    )

    lines.append(
        "Robotics Timing: "
        "AI_INFRASTRUCTURE_SIGNAL_ENGINE"
    )

    lines.append(
        "Quantum Timing: NONE"
    )

    lines.append(
        "Timing muda ranking fundamental: NÃO"
    )

    lines.append(
        "Timing muda composição fundamental: NÃO"
    )

    lines.append(
        "Timing gera SELL: NÃO"
    )

    lines.append(
        "Retorno futuro utilizado na decisão: NÃO"
    )

    lines.append(
        "=" * 100
    )

    return "\n".join(
        lines
    )


# ============================================================
# SALVAMENTO
# ============================================================

def save_reports(
    portfolio: pd.DataFrame,
    portfolio_file: Path = DEFAULT_CSV_FILE,
    robotics_file: Path = DEFAULT_ROBOTICS_FILE,
    quantum_file: Path = DEFAULT_QUANTUM_FILE,
    summary_file: Path = DEFAULT_SUMMARY_FILE,
) -> dict:
    """
    Salva os resultados.
    """

    validate_portfolio_report_input(
        portfolio
    )

    _ensure_output_directory()

    robotics, quantum = (
        split_portfolio(
            portfolio
        )
    )

    robotics_view = (
        build_robotics_view(
            robotics
        )
    )

    quantum_view = (
        build_quantum_view(
            quantum
        )
    )

    portfolio_file = Path(
        portfolio_file
    )

    robotics_file = Path(
        robotics_file
    )

    quantum_file = Path(
        quantum_file
    )

    summary_file = Path(
        summary_file
    )

    for path in [
        portfolio_file,
        robotics_file,
        quantum_file,
        summary_file,
    ]:

        path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

    portfolio.to_csv(
        portfolio_file,
        index=False,
        encoding="utf-8-sig",
    )

    robotics_view.to_csv(
        robotics_file,
        index=False,
        encoding="utf-8-sig",
    )

    quantum_view.to_csv(
        quantum_file,
        index=False,
        encoding="utf-8-sig",
    )

    summary = (
        build_executive_summary(
            portfolio
        )
    )

    summary_file.write_text(
        summary,
        encoding="utf-8",
    )

    return {
        "portfolio":
            portfolio_file,

        "robotics":
            robotics_file,

        "quantum":
            quantum_file,

        "summary":
            summary_file,
    }


# ============================================================
# EXIBIÇÃO
# ============================================================

def print_report(
    portfolio: pd.DataFrame,
) -> None:
    """
    Exibe relatório no terminal/GitHub Actions.
    """

    robotics, quantum = (
        split_portfolio(
            portfolio
        )
    )

    robotics_view = (
        build_robotics_view(
            robotics
        )
    )

    quantum_view = (
        build_quantum_view(
            quantum
        )
    )

    print()
    print(
        "=" * 110
    )

    print(
        "ROBOTICS_QUANTUM_SP500 — "
        "RELATÓRIO FINAL"
    )

    print(
        "=" * 110
    )

    print()
    print(
        "ROBOTICS — "
        "FINANCIAL STRENGTH TOP 5 "
        "+ TIMING"
    )

    print(
        "-" * 110
    )

    if robotics_view.empty:

        print(
            "Nenhuma empresa."
        )

    else:

        print(
            robotics_view.to_string(
                index=False
            )
        )

    print()
    print(
        "QUANTUM — "
        "GROWTH TOP 2"
    )

    print(
        "-" * 110
    )

    if quantum_view.empty:

        print(
            "Nenhuma empresa."
        )

    else:

        print(
            quantum_view.to_string(
                index=False
            )
        )

    print()
    print(
        "=" * 110
    )


# ============================================================
# CLASSE PRINCIPAL
# ============================================================

class ReportGenerator:
    """
    Gerador oficial do relatório.
    """

    def __init__(
        self,
    ) -> None:

        self.portfolio = (
            pd.DataFrame()
        )

        self.robotics = (
            pd.DataFrame()
        )

        self.quantum = (
            pd.DataFrame()
        )

        self.summary = ""

    def generate(
        self,
        portfolio: pd.DataFrame,
        save: bool = True,
        display: bool = True,
    ) -> dict:
        """
        Gera relatório final.
        """

        validate_portfolio_report_input(
            portfolio
        )

        self.portfolio = (
            portfolio.copy()
        )

        (
            self.robotics,
            self.quantum,
        ) = split_portfolio(
            self.portfolio
        )

        self.summary = (
            build_executive_summary(
                self.portfolio
            )
        )

        files = {}

        if save:

            files = save_reports(
                self.portfolio
            )

        if display:

            print_report(
                self.portfolio
            )

        return {
            "portfolio":
                self.portfolio.copy(),

            "robotics":
                self.robotics.copy(),

            "quantum":
                self.quantum.copy(),

            "summary":
                self.summary,

            "files":
                files,
        }


# ============================================================
# INTERFACE SIMPLIFICADA
# ============================================================

def generate_report(
    portfolio: pd.DataFrame,
    save: bool = True,
    display: bool = True,
) -> dict:
    """
    Interface simplificada.
    """

    generator = (
        ReportGenerator()
    )

    return generator.generate(
        portfolio=portfolio,
        save=save,
        display=display,
    )
