"""
ROBOTICS_QUANTUM_SP500
======================

RELATÓRIO EXECUTIVO POR E-MAIL

Responsabilidades deste módulo:

1. Receber o portfólio final produzido pelo Portfolio Engine.
2. Gerar resumo executivo em HTML para o corpo do e-mail.
3. Gerar relatório completo em PDF.
4. Anexar o PDF ao e-mail.
5. Enviar via Gmail utilizando GitHub Secrets.

IMPORTANTE
----------
Este módulo NÃO:

- seleciona empresas;
- recalcula fundamentos;
- altera ranking fundamental;
- recalcula timing;
- altera Signal Engine;
- cria sinal de venda;
- altera a arquitetura validada.

Secrets esperados:

EMAIL_USER
EMAIL_PASSWORD
EMAIL_TO
"""

from __future__ import annotations

import os
import smtplib
from datetime import datetime, timezone
from email.message import EmailMessage
from html import escape
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import (
    ParagraphStyle,
    getSampleStyleSheet,
)
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    PageBreak,
)

from config.settings import OUTPUTS_DIR


# =============================================================================
# CONFIGURAÇÃO
# =============================================================================

ROBOT_NAME = "ROBOTICS_QUANTUM_SP500"

PDF_FILENAME = (
    "relatorio_robotics_quantum_sp500.pdf"
)

PDF_PATH = (
    Path(OUTPUTS_DIR)
    /
    PDF_FILENAME
)

SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 465


# =============================================================================
# HELPERS
# =============================================================================

def _safe_text(
    value,
    default="-",
):
    """
    Converte valor para texto de forma segura.
    """

    if value is None:
        return default

    try:
        if pd.isna(value):
            return default
    except Exception:
        pass

    text = str(value).strip()

    if not text:
        return default

    return text


def _safe_float(
    value,
):
    """
    Converte valor para float.
    """

    try:

        if value is None:
            return np.nan

        value = float(value)

        if np.isfinite(value):
            return value

    except Exception:
        pass

    return np.nan


def _format_score(
    value,
    decimals=2,
):
    """
    Formata score.
    """

    value = _safe_float(value)

    if pd.isna(value):
        return "-"

    return f"{value:.{decimals}f}"


def _format_fundamental_score(
    value,
):
    """
    Fundamental score é armazenado normalmente
    entre 0 e 1.

    Exemplo:
    0.913889 -> 0.914
    """

    value = _safe_float(value)

    if pd.isna(value):
        return "-"

    return f"{value:.3f}"


def _format_percent(
    value,
    decimals=1,
):
    """
    Formata percentual sem assumir que o número
    esteja em escala decimal.
    """

    value = _safe_float(value)

    if pd.isna(value):
        return "-"

    return f"{value:.{decimals}f}%"


def _column(
    df: pd.DataFrame,
    name: str,
    default=np.nan,
):
    """
    Retorna uma coluna existente ou uma Series
    com valor padrão.
    """

    if name in df.columns:
        return df[name]

    return pd.Series(
        [default] * len(df),
        index=df.index,
    )


def _utc_now():
    """
    Horário UTC da geração.
    """

    return datetime.now(
        timezone.utc
    )


def _ensure_output_directory():
    """
    Garante diretório de saída.
    """

    Path(
        OUTPUTS_DIR
    ).mkdir(
        parents=True,
        exist_ok=True,
    )


# =============================================================================
# VALIDAÇÃO DO PORTFÓLIO
# =============================================================================

def validate_portfolio(
    portfolio: pd.DataFrame,
):
    """
    Valida somente a estrutura necessária
    para geração do relatório.

    Não recalcula qualquer decisão.
    """

    if portfolio is None:

        raise RuntimeError(
            "Portfolio recebido pelo relatório é None."
        )

    if not isinstance(
        portfolio,
        pd.DataFrame,
    ):

        raise TypeError(
            "Portfolio deve ser um pandas.DataFrame."
        )

    if portfolio.empty:

        raise RuntimeError(
            "Portfolio vazio."
        )

    required = [
        "ticker",
        "ranking_theme",
        "fundamental_position",
        "fundamental_factor",
        "fundamental_score",
        "entry_action",
    ]

    missing = [
        column
        for column in required
        if column not in portfolio.columns
    ]

    if missing:

        raise RuntimeError(
            "Portfolio sem colunas obrigatórias "
            "para o relatório: "
            f"{missing}"
        )

    themes = set(
        portfolio[
            "ranking_theme"
        ]
        .astype(str)
        .str.upper()
        .unique()
    )

    if "ROBOTICS" not in themes:

        raise RuntimeError(
            "Portfolio sem seleção ROBOTICS."
        )

    if "QUANTUM" not in themes:

        raise RuntimeError(
            "Portfolio sem seleção QUANTUM."
        )

    robotics = portfolio[
        portfolio[
            "ranking_theme"
        ]
        .astype(str)
        .str.upper()
        .eq("ROBOTICS")
    ]

    quantum = portfolio[
        portfolio[
            "ranking_theme"
        ]
        .astype(str)
        .str.upper()
        .eq("QUANTUM")
    ]

    if len(robotics) != 5:

        raise RuntimeError(
            "Relatório recebeu quantidade inválida "
            f"de Robotics: {len(robotics)}. "
            "Esperado: 5."
        )

    if len(quantum) != 2:

        raise RuntimeError(
            "Relatório recebeu quantidade inválida "
            f"de Quantum: {len(quantum)}. "
            "Esperado: 2."
        )

    return True


# =============================================================================
# SEPARAÇÃO DAS CARTEIRAS
# =============================================================================

def split_portfolio(
    portfolio: pd.DataFrame,
):
    """
    Separa Robotics e Quantum mantendo
    ranking fundamental.
    """

    robotics = (
        portfolio[
            portfolio[
                "ranking_theme"
            ]
            .astype(str)
            .str.upper()
            .eq("ROBOTICS")
        ]
        .copy()
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
        portfolio[
            portfolio[
                "ranking_theme"
            ]
            .astype(str)
            .str.upper()
            .eq("QUANTUM")
        ]
        .copy()
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

    return robotics, quantum


# =============================================================================
# RESUMO OPERACIONAL
# =============================================================================

def calculate_operational_summary(
    portfolio: pd.DataFrame,
):
    """
    Resume somente decisões já produzidas
    pelos motores anteriores.
    """

    robotics, quantum = (
        split_portfolio(
            portfolio
        )
    )

    if "signal_approved" in robotics.columns:

        approved = (
            robotics[
                "signal_approved"
            ]
            .fillna(False)
            .astype(bool)
        )

        robotics_approved = int(
            approved.sum()
        )

    else:

        robotics_approved = 0

    robotics_waiting = (
        len(robotics)
        -
        robotics_approved
    )

    unique_companies = int(
        portfolio[
            "ticker"
        ]
        .astype(str)
        .nunique()
    )

    return {
        "robotics_selected":
            len(robotics),

        "robotics_approved":
            robotics_approved,

        "robotics_waiting":
            robotics_waiting,

        "quantum_selected":
            len(quantum),

        "portfolio_theses":
            len(portfolio),

        "unique_companies":
            unique_companies,
    }


# =============================================================================
# HTML — CABEÇALHO
# =============================================================================

def _html_header(
    generated_at,
):
    """
    Cabeçalho visual do e-mail.
    """

    date_text = generated_at.strftime(
        "%d/%m/%Y %H:%M UTC"
    )

    return f"""
    <div style="
        font-family:Arial,Helvetica,sans-serif;
        max-width:980px;
        margin:auto;
        color:#1f2937;
    ">

        <div style="
            background:#111827;
            color:white;
            padding:24px;
            border-radius:10px 10px 0 0;
        ">

            <div style="
                font-size:25px;
                font-weight:bold;
            ">
                ROBOTICS_QUANTUM_SP500
            </div>

            <div style="
                margin-top:6px;
                font-size:15px;
                color:#d1d5db;
            ">
                Relatório Executivo de Seleção e Entrada
            </div>

            <div style="
                margin-top:10px;
                font-size:12px;
                color:#9ca3af;
            ">
                {escape(date_text)}
            </div>

        </div>
    """


# =============================================================================
# HTML — RESUMO
# =============================================================================

def _html_summary(
    summary,
):
    """
    Bloco de resumo executivo.
    """

    approved = (
        summary[
            "robotics_approved"
        ]
    )

    if approved > 0:

        status_text = (
            f"{approved} oportunidade(s) ROBOTICS "
            "com entrada aprovada."
        )

        status_background = "#dcfce7"
        status_color = "#166534"

    else:

        status_text = (
            "Nenhuma empresa ROBOTICS possui "
            "entrada final aprovada neste momento."
        )

        status_background = "#fef3c7"
        status_color = "#92400e"

    return f"""
        <div style="
            padding:22px;
            background:#ffffff;
            border-left:1px solid #e5e7eb;
            border-right:1px solid #e5e7eb;
        ">

            <h2 style="
                margin-top:0;
                font-size:19px;
            ">
                Resumo Executivo
            </h2>

            <div style="
                padding:14px;
                background:{status_background};
                color:{status_color};
                border-radius:7px;
                font-weight:bold;
                margin-bottom:18px;
            ">
                {escape(status_text)}
            </div>

            <table
                cellpadding="8"
                cellspacing="0"
                style="
                    border-collapse:collapse;
                    width:100%;
                    font-size:14px;
                "
            >

                <tr>
                    <td>
                        Robotics selecionadas
                    </td>

                    <td align="right">
                        <strong>
                            {summary["robotics_selected"]}
                        </strong>
                    </td>
                </tr>

                <tr>
                    <td>
                        Robotics com entrada aprovada
                    </td>

                    <td align="right">
                        <strong>
                            {summary["robotics_approved"]}
                        </strong>
                    </td>
                </tr>

                <tr>
                    <td>
                        Robotics aguardando timing
                    </td>

                    <td align="right">
                        <strong>
                            {summary["robotics_waiting"]}
                        </strong>
                    </td>
                </tr>

                <tr>
                    <td>
                        Quantum selecionadas
                    </td>

                    <td align="right">
                        <strong>
                            {summary["quantum_selected"]}
                        </strong>
                    </td>
                </tr>

                <tr>
                    <td>
                        Teses selecionadas
                    </td>

                    <td align="right">
                        <strong>
                            {summary["portfolio_theses"]}
                        </strong>
                    </td>
                </tr>

                <tr>
                    <td>
                        Empresas únicas
                    </td>

                    <td align="right">
                        <strong>
                            {summary["unique_companies"]}
                        </strong>
                    </td>
                </tr>

            </table>

        </div>
    """


# =============================================================================
# HTML — ROBOTICS
# =============================================================================

def _html_robotics_table(
    robotics: pd.DataFrame,
):
    """
    Tabela ROBOTICS para o corpo do e-mail.
    """

    rows = []

    for _, row in robotics.iterrows():

        position = _safe_text(
            row.get(
                "fundamental_position"
            )
        )

        ticker = escape(
            _safe_text(
                row.get(
                    "ticker"
                )
            )
        )

        fundamental = (
            _format_fundamental_score(
                row.get(
                    "fundamental_score"
                )
            )
        )

        institutional = (
            _format_score(
                row.get(
                    "institutional_score"
                )
            )
        )

        technical = (
            _format_score(
                row.get(
                    "technical_entry_score"
                )
            )
        )

        timing = (
            _format_score(
                row.get(
                    "entry_timing_score"
                )
            )
        )

        final_score = (
            _format_score(
                row.get(
                    "final_score"
                )
            )
        )

        timing_status = escape(
            _safe_text(
                row.get(
                    "timing_status"
                )
            )
        )

        action = escape(
            _safe_text(
                row.get(
                    "entry_action"
                )
            )
        )

        rows.append(
            f"""
            <tr>
                <td>{position}</td>
                <td><strong>{ticker}</strong></td>
                <td>{fundamental}</td>
                <td>{institutional}</td>
                <td>{technical}</td>
                <td>{timing}</td>
                <td>{final_score}</td>
                <td>{timing_status}</td>
                <td><strong>{action}</strong></td>
            </tr>
            """
        )

    body = "".join(
        rows
    )

    return f"""
        <div style="
            padding:22px;
            background:#ffffff;
            border-left:1px solid #e5e7eb;
            border-right:1px solid #e5e7eb;
        ">

            <h2 style="
                margin-top:0;
                font-size:19px;
            ">
                ROBOTICS — Financial Strength Top 5
            </h2>

            <p style="
                font-size:13px;
                color:#4b5563;
            ">
                A seleção fundamental define quais empresas
                pertencem ao Top 5. O timing é utilizado
                exclusivamente para decidir o momento de
                entrada ou novo aporte.
            </p>

            <div style="overflow-x:auto;">

                <table
                    cellpadding="8"
                    cellspacing="0"
                    style="
                        border-collapse:collapse;
                        width:100%;
                        font-size:12px;
                    "
                >

                    <thead>

                        <tr style="
                            background:#f3f4f6;
                        ">

                            <th>Pos.</th>
                            <th>Ticker</th>
                            <th>Fund.</th>
                            <th>Inst.</th>
                            <th>Técnico</th>
                            <th>Timing</th>
                            <th>Final</th>
                            <th>Status</th>
                            <th>Decisão</th>

                        </tr>

                    </thead>

                    <tbody>
                        {body}
                    </tbody>

                </table>

            </div>

        </div>
    """


# =============================================================================
# HTML — QUANTUM
# =============================================================================

def _html_quantum_table(
    quantum: pd.DataFrame,
):
    """
    Tabela QUANTUM para o corpo do e-mail.
    """

    rows = []

    for _, row in quantum.iterrows():

        position = _safe_text(
            row.get(
                "fundamental_position"
            )
        )

        ticker = escape(
            _safe_text(
                row.get(
                    "ticker"
                )
            )
        )

        company = escape(
            _safe_text(
                row.get(
                    "company"
                )
            )
        )

        fundamental = (
            _format_fundamental_score(
                row.get(
                    "fundamental_score"
                )
            )
        )

        action = escape(
            _safe_text(
                row.get(
                    "entry_action"
                )
            )
        )

        rows.append(
            f"""
            <tr>
                <td>{position}</td>
                <td><strong>{ticker}</strong></td>
                <td>{company}</td>
                <td>{fundamental}</td>
                <td><strong>{action}</strong></td>
            </tr>
            """
        )

    body = "".join(
        rows
    )

    return f"""
        <div style="
            padding:22px;
            background:#ffffff;
            border-left:1px solid #e5e7eb;
            border-right:1px solid #e5e7eb;
        ">

            <h2 style="
                margin-top:0;
                font-size:19px;
            ">
                QUANTUM — Growth Top 2
            </h2>

            <p style="
                font-size:13px;
                color:#4b5563;
            ">
                Quantum utiliza exclusivamente a seleção
                fundamental validada. O AI Infrastructure
                Timing Engine não é utilizado neste tema.
            </p>

            <table
                cellpadding="8"
                cellspacing="0"
                style="
                    border-collapse:collapse;
                    width:100%;
                    font-size:13px;
                "
            >

                <thead>

                    <tr style="
                        background:#f3f4f6;
                    ">

                        <th>Pos.</th>
                        <th>Ticker</th>
                        <th>Empresa</th>
                        <th>Growth Score</th>
                        <th>Decisão</th>

                    </tr>

                </thead>

                <tbody>
                    {body}
                </tbody>

            </table>

        </div>
    """


# =============================================================================
# HTML — RODAPÉ
# =============================================================================

def _html_footer():
    """
    Rodapé do e-mail.
    """

    return """
        <div style="
            padding:20px;
            background:#f9fafb;
            border:1px solid #e5e7eb;
            border-radius:0 0 10px 10px;
            font-size:12px;
            color:#6b7280;
        ">

            <strong>Arquitetura do robô</strong>

            <br><br>

            ROBOTICS:
            Financial Strength Top 5 +
            AI Infrastructure Signal Engine
            exclusivamente para entrada/aporte.

            <br><br>

            QUANTUM:
            Growth Top 2.
            Timing técnico não utilizado.

            <br><br>

            O timing não altera o ranking fundamental,
            não remove empresas selecionadas e não
            gera sinal de venda.

            <br><br>

            Relatório gerado automaticamente pelo
            ROBOTICS_QUANTUM_SP500.

        </div>

    </div>
    """


# =============================================================================
# GERAR HTML COMPLETO
# =============================================================================

def build_html_report(
    portfolio: pd.DataFrame,
):
    """
    Gera corpo HTML completo do e-mail.
    """

    validate_portfolio(
        portfolio
    )

    generated_at = (
        _utc_now()
    )

    robotics, quantum = (
        split_portfolio(
            portfolio
        )
    )

    summary = (
        calculate_operational_summary(
            portfolio
        )
    )

    html = "".join(
        [
            _html_header(
                generated_at
            ),
            _html_summary(
                summary
            ),
            _html_robotics_table(
                robotics
            ),
            _html_quantum_table(
                quantum
            ),
            _html_footer(),
        ]
    )

    return html


# =============================================================================
# PDF — ESTILOS
# =============================================================================

def _pdf_styles():
    """
    Estilos utilizados no PDF.
    """

    styles = (
        getSampleStyleSheet()
    )

    title = ParagraphStyle(
        "RobotTitle",
        parent=styles[
            "Title"
        ],
        fontName="Helvetica-Bold",
        fontSize=19,
        leading=23,
        alignment=TA_CENTER,
        spaceAfter=8,
    )

    subtitle = ParagraphStyle(
        "RobotSubtitle",
        parent=styles[
            "Normal"
        ],
        fontName="Helvetica",
        fontSize=10,
        leading=14,
        alignment=TA_CENTER,
        spaceAfter=14,
    )

    heading = ParagraphStyle(
        "RobotHeading",
        parent=styles[
            "Heading2"
        ],
        fontName="Helvetica-Bold",
        fontSize=14,
        leading=17,
        alignment=TA_LEFT,
        spaceBefore=8,
        spaceAfter=8,
    )

    normal = ParagraphStyle(
        "RobotNormal",
        parent=styles[
            "Normal"
        ],
        fontName="Helvetica",
        fontSize=9,
        leading=13,
        alignment=TA_LEFT,
    )

    small = ParagraphStyle(
        "RobotSmall",
        parent=styles[
            "Normal"
        ],
        fontName="Helvetica",
        fontSize=7.5,
        leading=10,
        alignment=TA_LEFT,
    )

    return {
        "title":
            title,

        "subtitle":
            subtitle,

        "heading":
            heading,

        "normal":
            normal,

        "small":
            small,
    }


# =============================================================================
# PDF — TABELA ROBOTICS
# =============================================================================

def _pdf_robotics_table(
    robotics: pd.DataFrame,
    styles,
):
    """
    Constrói tabela ROBOTICS do PDF.
    """

    data = [
        [
            "Pos.",
            "Ticker",
            "Fund.",
            "Inst.",
            "Técnico",
            "Timing",
            "Final",
            "Status",
            "Decisão",
        ]
    ]

    for _, row in robotics.iterrows():

        data.append(
            [
                _safe_text(
                    row.get(
                        "fundamental_position"
                    )
                ),

                _safe_text(
                    row.get(
                        "ticker"
                    )
                ),

                _format_fundamental_score(
                    row.get(
                        "fundamental_score"
                    )
                ),

                _format_score(
                    row.get(
                        "institutional_score"
                    )
                ),

                _format_score(
                    row.get(
                        "technical_entry_score"
                    )
                ),

                _format_score(
                    row.get(
                        "entry_timing_score"
                    )
                ),

                _format_score(
                    row.get(
                        "final_score"
                    )
                ),

                Paragraph(
                    _safe_text(
                        row.get(
                            "timing_status"
                        )
                    ),
                    styles[
                        "small"
                    ],
                ),

                Paragraph(
                    _safe_text(
                        row.get(
                            "entry_action"
                        )
                    ),
                    styles[
                        "small"
                    ],
                ),
            ]
        )

    table = Table(
        data,
        repeatRows=1,
        colWidths=[
            1.0 * cm,
            1.4 * cm,
            1.5 * cm,
            1.5 * cm,
            1.6 * cm,
            1.6 * cm,
            1.5 * cm,
            4.0 * cm,
            4.2 * cm,
        ],
    )

    table.setStyle(
        TableStyle(
            [
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, 0),
                    colors.HexColor(
                        "#E5E7EB"
                    ),
                ),

                (
                    "FONTNAME",
                    (0, 0),
                    (-1, 0),
                    "Helvetica-Bold",
                ),

                (
                    "FONTSIZE",
                    (0, 0),
                    (-1, -1),
                    7,
                ),

                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "MIDDLE",
                ),

                (
                    "ALIGN",
                    (0, 0),
                    (6, -1),
                    "CENTER",
                ),

                (
                    "GRID",
                    (0, 0),
                    (-1, -1),
                    0.3,
                    colors.HexColor(
                        "#D1D5DB"
                    ),
                ),

                (
                    "ROWBACKGROUNDS",
                    (0, 1),
                    (-1, -1),
                    [
                        colors.white,
                        colors.HexColor(
                            "#F9FAFB"
                        ),
                    ],
                ),

                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    5,
                ),

                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    5,
                ),
            ]
        )
    )

    return table


# =============================================================================
# PDF — TABELA QUANTUM
# =============================================================================

def _pdf_quantum_table(
    quantum: pd.DataFrame,
    styles,
):
    """
    Constrói tabela QUANTUM do PDF.
    """

    data = [
        [
            "Pos.",
            "Ticker",
            "Empresa",
            "Growth Score",
            "Decisão",
        ]
    ]

    for _, row in quantum.iterrows():

        data.append(
            [
                _safe_text(
                    row.get(
                        "fundamental_position"
                    )
                ),

                _safe_text(
                    row.get(
                        "ticker"
                    )
                ),

                Paragraph(
                    _safe_text(
                        row.get(
                            "company"
                        )
                    ),
                    styles[
                        "small"
                    ],
                ),

                _format_fundamental_score(
                    row.get(
                        "fundamental_score"
                    )
                ),

                Paragraph(
                    _safe_text(
                        row.get(
                            "entry_action"
                        )
                    ),
                    styles[
                        "small"
                    ],
                ),
            ]
        )

    table = Table(
        data,
        repeatRows=1,
        colWidths=[
            1.2 * cm,
            1.8 * cm,
            5.0 * cm,
            2.5 * cm,
            5.0 * cm,
        ],
    )

    table.setStyle(
        TableStyle(
            [
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, 0),
                    colors.HexColor(
                        "#E5E7EB"
                    ),
                ),

                (
                    "FONTNAME",
                    (0, 0),
                    (-1, 0),
                    "Helvetica-Bold",
                ),

                (
                    "FONTSIZE",
                    (0, 0),
                    (-1, -1),
                    8,
                ),

                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "MIDDLE",
                ),

                (
                    "ALIGN",
                    (0, 0),
                    (1, -1),
                    "CENTER",
                ),

                (
                    "ALIGN",
                    (3, 0),
                    (3, -1),
                    "CENTER",
                ),

                (
                    "GRID",
                    (0, 0),
                    (-1, -1),
                    0.3,
                    colors.HexColor(
                        "#D1D5DB"
                    ),
                ),

                (
                    "ROWBACKGROUNDS",
                    (0, 1),
                    (-1, -1),
                    [
                        colors.white,
                        colors.HexColor(
                            "#F9FAFB"
                        ),
                    ],
                ),

                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    6,
                ),

                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    6,
                ),
            ]
        )
    )

    return table


# =============================================================================
# GERAR PDF
# =============================================================================

def generate_pdf(
    portfolio: pd.DataFrame,
    output_path: Optional[Path] = None,
):
    """
    Gera PDF executivo completo.
    """

    validate_portfolio(
        portfolio
    )

    _ensure_output_directory()

    if output_path is None:

        output_path = (
            PDF_PATH
        )

    output_path = Path(
        output_path
    )

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    robotics, quantum = (
        split_portfolio(
            portfolio
        )
    )

    summary = (
        calculate_operational_summary(
            portfolio
        )
    )

    styles = (
        _pdf_styles()
    )

    document = (
        SimpleDocTemplate(
            str(
                output_path
            ),
            pagesize=landscape(
                A4
            ),
            rightMargin=1.2 * cm,
            leftMargin=1.2 * cm,
            topMargin=1.2 * cm,
            bottomMargin=1.2 * cm,
            title=(
                "ROBOTICS_QUANTUM_SP500 "
                "— Relatório Executivo"
            ),
            author=(
                "ROBOTICS_QUANTUM_SP500"
            ),
        )
    )

    story = []

    generated_at = (
        _utc_now()
    )

    # -------------------------------------------------------------------------
    # Título
    # -------------------------------------------------------------------------

    story.append(
        Paragraph(
            "ROBOTICS_QUANTUM_SP500",
            styles[
                "title"
            ],
        )
    )

    story.append(
        Paragraph(
            (
                "Relatório Executivo de Seleção "
                "e Momento de Entrada"
            ),
            styles[
                "subtitle"
            ],
        )
    )

    story.append(
        Paragraph(
            generated_at.strftime(
                "Gerado em %d/%m/%Y às %H:%M UTC"
            ),
            styles[
                "subtitle"
            ],
        )
    )

    story.append(
        Spacer(
            1,
            0.25 * cm,
        )
    )

    # -------------------------------------------------------------------------
    # Resumo executivo
    # -------------------------------------------------------------------------

    story.append(
        Paragraph(
            "Resumo Executivo",
            styles[
                "heading"
            ],
        )
    )

    if (
        summary[
            "robotics_approved"
        ]
        >
        0
    ):

        operational_text = (
            f"{summary['robotics_approved']} "
            "empresa(s) ROBOTICS possui(em) "
            "entrada/aporte aprovado pelo "
            "Signal Engine."
        )

    else:

        operational_text = (
            "Nenhuma empresa ROBOTICS possui "
            "entrada final aprovada neste momento."
        )

    story.append(
        Paragraph(
            operational_text,
            styles[
                "normal"
            ],
        )
    )

    story.append(
        Spacer(
            1,
            0.25 * cm,
        )
    )

    summary_data = [
        [
            "Indicador",
            "Resultado",
        ],
        [
            "Robotics selecionadas",
            str(
                summary[
                    "robotics_selected"
                ]
            ),
        ],
        [
            "Robotics com entrada aprovada",
            str(
                summary[
                    "robotics_approved"
                ]
            ),
        ],
        [
            "Robotics aguardando timing",
            str(
                summary[
                    "robotics_waiting"
                ]
            ),
        ],
        [
            "Quantum selecionadas",
            str(
                summary[
                    "quantum_selected"
                ]
            ),
        ],
        [
            "Teses selecionadas",
            str(
                summary[
                    "portfolio_theses"
                ]
            ),
        ],
        [
            "Empresas únicas",
            str(
                summary[
                    "unique_companies"
                ]
            ),
        ],
    ]

    summary_table = Table(
        summary_data,
        colWidths=[
            7.0 * cm,
            3.0 * cm,
        ],
    )

    summary_table.setStyle(
        TableStyle(
            [
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, 0),
                    colors.HexColor(
                        "#E5E7EB"
                    ),
                ),

                (
                    "FONTNAME",
                    (0, 0),
                    (-1, 0),
                    "Helvetica-Bold",
                ),

                (
                    "GRID",
                    (0, 0),
                    (-1, -1),
                    0.3,
                    colors.HexColor(
                        "#D1D5DB"
                    ),
                ),

                (
                    "FONTSIZE",
                    (0, 0),
                    (-1, -1),
                    9,
                ),

                (
                    "ALIGN",
                    (1, 0),
                    (1, -1),
                    "CENTER",
                ),

                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    5,
                ),

                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    5,
                ),
            ]
        )
    )

    story.append(
        summary_table
    )

    story.append(
        Spacer(
            1,
            0.5 * cm,
        )
    )

    # -------------------------------------------------------------------------
    # Robotics
    # -------------------------------------------------------------------------

    story.append(
        Paragraph(
            "ROBOTICS — Financial Strength Top 5",
            styles[
                "heading"
            ],
        )
    )

    story.append(
        Paragraph(
            (
                "A seleção fundamental determina "
                "as cinco empresas do tema. "
                "O AI Infrastructure Signal Engine "
                "é utilizado somente para avaliar "
                "o momento de entrada ou novo aporte."
            ),
            styles[
                "normal"
            ],
        )
    )

    story.append(
        Spacer(
            1,
            0.25 * cm,
        )
    )

    story.append(
        _pdf_robotics_table(
            robotics,
            styles,
        )
    )

    story.append(
        Spacer(
            1,
            0.5 * cm,
        )
    )

    # -------------------------------------------------------------------------
    # Quantum
    # -------------------------------------------------------------------------

    story.append(
        Paragraph(
            "QUANTUM — Growth Top 2",
            styles[
                "heading"
            ],
        )
    )

    story.append(
        Paragraph(
            (
                "Quantum utiliza exclusivamente "
                "o ranking fundamental Growth Top 2. "
                "O timing técnico não é utilizado "
                "neste tema."
            ),
            styles[
                "normal"
            ],
        )
    )

    story.append(
        Spacer(
            1,
            0.25 * cm,
        )
    )

    story.append(
        _pdf_quantum_table(
            quantum,
            styles,
        )
    )

    story.append(
        PageBreak()
    )

    # -------------------------------------------------------------------------
    # Arquitetura
    # -------------------------------------------------------------------------

    story.append(
        Paragraph(
            "Arquitetura e Regras Preservadas",
            styles[
                "heading"
            ],
        )
    )

    architecture_lines = [
        (
            "Universo: somente empresas pertencentes "
            "ao S&P 500 e classificadas nos temas "
            "Robotics e/ou Quantum Computing."
        ),

        (
            "Robotics: Financial Strength Top 5."
        ),

        (
            "Robotics Timing: AI Infrastructure "
            "Signal Engine utilizado exclusivamente "
            "para entrada e novo aporte."
        ),

        (
            "Quantum: Growth Top 2."
        ),

        (
            "Quantum: nenhuma camada de timing "
            "técnico é aplicada."
        ),

        (
            "O timing não altera a seleção "
            "fundamental."
        ),

        (
            "O timing não altera o ranking "
            "fundamental."
        ),

        (
            "O timing não gera sinal de venda."
        ),

        (
            "Retornos futuros não participam "
            "da geração dos sinais."
        ),
    ]

    for line in architecture_lines:

        story.append(
            Paragraph(
                f"• {line}",
                styles[
                    "normal"
                ],
            )
        )

        story.append(
            Spacer(
                1,
                0.12 * cm,
            )
        )

    story.append(
        Spacer(
            1,
            0.4 * cm,
        )
    )

    story.append(
        Paragraph(
            (
                "<b>Interpretação:</b> "
                "uma empresa pode permanecer "
                "selecionada fundamentalmente "
                "mesmo quando o Signal Engine "
                "determina que ainda não é o "
                "momento adequado para novo aporte."
            ),
            styles[
                "normal"
            ],
        )
    )

    # -------------------------------------------------------------------------
    # Construir PDF
    # -------------------------------------------------------------------------

    document.build(
        story
    )

    if not output_path.exists():

        raise RuntimeError(
            "PDF não foi criado."
        )

    if output_path.stat().st_size <= 0:

        raise RuntimeError(
            "PDF criado com tamanho inválido."
        )

    return output_path


# =============================================================================
# CONFIGURAÇÃO DO E-MAIL
# =============================================================================

def get_email_configuration():
    """
    Lê credenciais exclusivamente das
    variáveis de ambiente / GitHub Secrets.
    """

    email_user = (
        os.getenv(
            "EMAIL_USER",
            "",
        )
        .strip()
    )

    email_password = (
        os.getenv(
            "EMAIL_PASSWORD",
            "",
        )
        .strip()
    )

    email_to = (
        os.getenv(
            "EMAIL_TO",
            "",
        )
        .strip()
    )

    missing = []

    if not email_user:
        missing.append(
            "EMAIL_USER"
        )

    if not email_password:
        missing.append(
            "EMAIL_PASSWORD"
        )

    if not email_to:
        missing.append(
            "EMAIL_TO"
        )

    if missing:

        raise RuntimeError(
            "Secrets de e-mail ausentes: "
            +
            ", ".join(
                missing
            )
        )

    return (
        email_user,
        email_password,
        email_to,
    )


# =============================================================================
# ASSUNTO DO E-MAIL
# =============================================================================

def build_email_subject(
    portfolio: pd.DataFrame,
):
    """
    Assunto curto e informativo.
    """

    summary = (
        calculate_operational_summary(
            portfolio
        )
    )

    today = (
        _utc_now()
        .strftime(
            "%d/%m/%Y"
        )
    )

    approved = (
        summary[
            "robotics_approved"
        ]
    )

    if approved > 0:

        status = (
            f"{approved} entrada(s) ROBOTICS"
        )

    else:

        status = (
            "Robotics aguardando timing"
        )

    return (
        f"{ROBOT_NAME} | "
        f"{today} | "
        f"{status}"
    )


# =============================================================================
# ENVIAR E-MAIL
# =============================================================================

def send_email(
    portfolio: pd.DataFrame,
    pdf_path: Path,
):
    """
    Envia resumo HTML + PDF anexo.
    """

    (
        email_user,
        email_password,
        email_to,
    ) = (
        get_email_configuration()
    )

    html_report = (
        build_html_report(
            portfolio
        )
    )

    subject = (
        build_email_subject(
            portfolio
        )
    )

    message = (
        EmailMessage()
    )

    message[
        "Subject"
    ] = subject

    message[
        "From"
    ] = email_user

    message[
        "To"
    ] = email_to

    message.set_content(
        (
            "ROBOTICS_QUANTUM_SP500\n\n"
            "Este e-mail contém o relatório "
            "executivo do robô.\n\n"
            "Para melhor visualização, utilize "
            "um cliente de e-mail compatível "
            "com HTML.\n"
        )
    )

    message.add_alternative(
        html_report,
        subtype="html",
    )

    pdf_path = Path(
        pdf_path
    )

    if not pdf_path.exists():

        raise FileNotFoundError(
            f"PDF não encontrado: "
            f"{pdf_path}"
        )

    with open(
        pdf_path,
        "rb",
    ) as file:

        pdf_data = (
            file.read()
        )

    message.add_attachment(
        pdf_data,
        maintype="application",
        subtype="pdf",
        filename=(
            pdf_path.name
        ),
    )

    with smtplib.SMTP_SSL(
        SMTP_HOST,
        SMTP_PORT,
    ) as smtp:

        smtp.login(
            email_user,
            email_password,
        )

        smtp.send_message(
            message
        )

    return True


# =============================================================================
# FACHADA PRINCIPAL
# =============================================================================

class EmailReport:
    """
    Interface oficial utilizada pelo main.py.
    """

    @staticmethod
    def generate_and_send(
        portfolio: pd.DataFrame,
    ):
        """
        Executa exclusivamente a camada de relatório:

        1. valida o portfólio;
        2. gera PDF;
        3. gera HTML;
        4. envia e-mail;
        5. retorna informações da execução.

        Nenhum motor de investimento é recalculado.
        """

        validate_portfolio(
            portfolio
        )

        _ensure_output_directory()

        print(
            "\n"
            +
            "=" * 100
        )

        print(
            "RELATÓRIO POR E-MAIL"
        )

        print(
            "=" * 100
        )

        print(
            "Gerando PDF..."
        )

        pdf_path = (
            generate_pdf(
                portfolio
            )
        )

        print(
            f"PDF: {pdf_path}"
        )

        print(
            "Preparando resumo HTML..."
        )

        # Geração explícita para validar
        # o HTML antes do envio.
        build_html_report(
            portfolio
        )

        print(
            "Enviando e-mail..."
        )

        send_email(
            portfolio,
            pdf_path,
        )

        print(
            "E-mail enviado com sucesso."
        )

        print(
            "=" * 100
        )

        return {
            "email_sent":
                True,

            "pdf_path":
                str(
                    pdf_path
                ),

            "pdf_filename":
                pdf_path.name,
        }


# =============================================================================
# ALIAS FUNCIONAL
# =============================================================================

def generate_and_send_email_report(
    portfolio: pd.DataFrame,
):
    """
    Interface funcional alternativa.
    """

    return (
        EmailReport
        .generate_and_send(
            portfolio
        )
    )
