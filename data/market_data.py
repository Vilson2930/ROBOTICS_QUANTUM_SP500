"""
ROBOTICS_QUANTUM_SP500
======================

Market Data — Robotics Timing Layer.

RESPONSABILIDADE
----------------
Baixar e preparar histórico de preços SOMENTE para as empresas
Robotics que já passaram pela seleção fundamental.

Pipeline:

S&P 500
    ↓
Robotics / Quantum
    ↓
Fundamentos
    ↓
ROBOTICS Financial Strength Top 5
    ↓
MARKET DATA  <-- ESTE MÓDULO
    ↓
Technical Indicators
    ↓
Institutional Score
    ↓
Technical Score
    ↓
Entry Timing
    ↓
Signal Engine

IMPORTANTE
----------
- Market Data NÃO escolhe empresas.
- Market Data NÃO altera ranking fundamental.
- Market Data NÃO gera venda.
- Quantum NÃO depende deste módulo para sua seleção.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Iterable, List, Optional

import numpy as np
import pandas as pd
import yfinance as yf

from config.settings import (
    PRICE_HISTORY_YEARS,
    USE_ADJUSTED_PRICES,
)


# =============================================================================
# CONFIGURAÇÃO
# =============================================================================

MINIMUM_PRICE_ROWS = 250

REQUIRED_OUTPUT_COLUMNS = [
    "ticker",
    "date",
    "open",
    "high",
    "low",
    "close",
    "volume",
]


# =============================================================================
# TICKERS
# =============================================================================

def normalize_ticker(
    ticker,
) -> str:
    """
    Normaliza ticker para uso no Yahoo Finance.
    """

    if ticker is None:
        raise ValueError(
            "Ticker ausente."
        )

    ticker = (
        str(ticker)
        .strip()
        .upper()
    )

    if not ticker:
        raise ValueError(
            "Ticker vazio."
        )

    # Yahoo utiliza hífen em tickers como BRK-B.

    ticker = ticker.replace(
        ".",
        "-",
    )

    return ticker


def extract_robotics_tickers(
    fundamental_selection: pd.DataFrame,
) -> List[str]:
    """
    Extrai SOMENTE os tickers selecionados
    fundamentalmente em Robotics.
    """

    if not isinstance(
        fundamental_selection,
        pd.DataFrame,
    ):
        raise TypeError(
            "fundamental_selection deve ser DataFrame."
        )

    if fundamental_selection.empty:
        raise ValueError(
            "Seleção fundamental vazia."
        )

    required = {
        "ticker",
        "ranking_theme",
        "selected_fundamentally",
    }

    missing = (
        required
        - set(
            fundamental_selection.columns
        )
    )

    if missing:
        raise ValueError(
            "Colunas ausentes na seleção fundamental: "
            f"{sorted(missing)}"
        )

    robotics = fundamental_selection.loc[
        (
            fundamental_selection[
                "ranking_theme"
            ]
            .astype(str)
            .str.upper()
            == "ROBOTICS"
        )
        &
        (
            fundamental_selection[
                "selected_fundamentally"
            ]
            .fillna(False)
            .astype(bool)
        )
    ].copy()

    if robotics.empty:
        raise RuntimeError(
            "Nenhuma empresa Robotics "
            "fundamentalmente selecionada."
        )

    tickers = sorted(
        {
            normalize_ticker(
                ticker
            )
            for ticker in robotics[
                "ticker"
            ]
        }
    )

    # Política congelada:
    # Robotics possui no máximo 5 selecionadas.

    if len(tickers) > 5:
        raise AssertionError(
            "Market Data recebeu mais de 5 "
            "empresas Robotics."
        )

    return tickers


# =============================================================================
# DOWNLOAD DE UM TICKER
# =============================================================================

def download_ticker_history(
    ticker: str,
    start: Optional[pd.Timestamp] = None,
    end: Optional[pd.Timestamp] = None,
) -> pd.DataFrame:
    """
    Baixa histórico diário de um ticker.
    """

    ticker = normalize_ticker(
        ticker
    )

    if end is None:

        end = pd.Timestamp(
            datetime.now(
                timezone.utc
            ).date()
        ) + pd.Timedelta(
            days=1
        )

    else:

        end = pd.Timestamp(
            end
        )

    if start is None:

        start = (
            end
            - pd.DateOffset(
                years=PRICE_HISTORY_YEARS
            )
            - pd.Timedelta(
                days=30
            )
        )

    else:

        start = pd.Timestamp(
            start
        )

    if start >= end:
        raise ValueError(
            f"{ticker}: start deve ser anterior a end."
        )

    # -------------------------------------------------------------------------
    # auto_adjust
    # -------------------------------------------------------------------------
    #
    # Quando USE_ADJUSTED_PRICES=True, o Yahoo ajusta OHLC
    # por splits/dividendos.
    #
    # Isso mantém consistência entre as séries utilizadas
    # pelos indicadores técnicos.
    # -------------------------------------------------------------------------

    data = yf.download(
        ticker,
        start=start.strftime(
            "%Y-%m-%d"
        ),
        end=end.strftime(
            "%Y-%m-%d"
        ),
        auto_adjust=USE_ADJUSTED_PRICES,
        actions=False,
        progress=False,
        threads=False,
    )

    if data is None or data.empty:
        raise RuntimeError(
            f"{ticker}: Yahoo Finance retornou "
            "histórico vazio."
        )

    # yfinance pode retornar MultiIndex mesmo
    # para apenas um ticker dependendo da versão.

    if isinstance(
        data.columns,
        pd.MultiIndex,
    ):

        if ticker in data.columns.get_level_values(
            -1
        ):

            try:
                data = data.xs(
                    ticker,
                    axis=1,
                    level=-1,
                )

            except Exception:
                pass

        if isinstance(
            data.columns,
            pd.MultiIndex,
        ):

            data.columns = [
                column[0]
                if isinstance(
                    column,
                    tuple,
                )
                else column
                for column in data.columns
            ]

    data = (
        data
        .reset_index()
        .copy()
    )

    rename_map = {
        "Date":
            "date",

        "Datetime":
            "date",

        "Open":
            "open",

        "High":
            "high",

        "Low":
            "low",

        "Close":
            "close",

        "Adj Close":
            "adj_close",

        "Volume":
            "volume",
    }

    data = data.rename(
        columns=rename_map
    )

    required = {
        "date",
        "open",
        "high",
        "low",
        "close",
        "volume",
    }

    missing = (
        required
        - set(
            data.columns
        )
    )

    if missing:
        raise RuntimeError(
            f"{ticker}: colunas de mercado ausentes: "
            f"{sorted(missing)}"
        )

    data["date"] = pd.to_datetime(
        data["date"],
        errors="coerce",
    )

    # Remover timezone para manter DataFrame
    # compatível com os módulos do scanner.

    try:

        data["date"] = (
            data["date"]
            .dt.tz_localize(
                None
            )
        )

    except TypeError:
        pass

    numeric_columns = [
        "open",
        "high",
        "low",
        "close",
        "volume",
    ]

    for column in numeric_columns:

        data[column] = pd.to_numeric(
            data[column],
            errors="coerce",
        )

        data[column] = (
            data[column]
            .replace(
                [
                    np.inf,
                    -np.inf,
                ],
                np.nan,
            )
        )

    data = data.dropna(
        subset=[
            "date",
            "open",
            "high",
            "low",
            "close",
            "volume",
        ]
    )

    data = data.loc[
        data["close"] > 0
    ].copy()

    data = data.loc[
        data["high"] >= data["low"]
    ].copy()

    data["ticker"] = (
        ticker
    )

    data = (
        data[
            REQUIRED_OUTPUT_COLUMNS
        ]
        .sort_values(
            "date"
        )
        .drop_duplicates(
            subset=[
                "ticker",
                "date",
            ],
            keep="last",
        )
        .reset_index(
            drop=True
        )
    )

    if len(data) < MINIMUM_PRICE_ROWS:
        raise RuntimeError(
            f"{ticker}: histórico insuficiente "
            f"({len(data)} pregões)."
        )

    return data


# =============================================================================
# DOWNLOAD DO UNIVERSO ROBOTICS SELECIONADO
# =============================================================================

def download_price_history(
    tickers: Iterable[str],
    start: Optional[pd.Timestamp] = None,
    end: Optional[pd.Timestamp] = None,
) -> pd.DataFrame:
    """
    Baixa histórico de todos os tickers recebidos.
    """

    normalized = sorted(
        {
            normalize_ticker(
                ticker
            )
            for ticker in tickers
        }
    )

    if not normalized:
        raise ValueError(
            "Nenhum ticker recebido."
        )

    if len(normalized) > 5:
        raise AssertionError(
            "Timing Robotics recebeu mais de "
            "5 empresas."
        )

    frames = []
    errors = []

    total = len(
        normalized
    )

    for position, ticker in enumerate(
        normalized,
        start=1,
    ):

        print(
            f"[{position:02d}/{total:02d}] "
            f"Market Data: {ticker}"
        )

        try:

            history = (
                download_ticker_history(
                    ticker=ticker,
                    start=start,
                    end=end,
                )
            )

            frames.append(
                history
            )

            print(
                f"   OK — {len(history)} pregões"
            )

        except Exception as exc:

            errors.append(
                {
                    "ticker":
                        ticker,

                    "error":
                        str(exc),
                }
            )

            print(
                f"   ERRO — {exc}"
            )

    if not frames:
        raise RuntimeError(
            "Nenhum histórico de preços "
            "foi obtido."
        )

    result = pd.concat(
        frames,
        ignore_index=True,
    )

    result = (
        result
        .sort_values(
            [
                "ticker",
                "date",
            ]
        )
        .reset_index(
            drop=True
        )
    )

    if errors:

        print(
            "\nFalhas de Market Data:"
        )

        print(
            pd.DataFrame(
                errors
            ).to_string(
                index=False
            )
        )

    return result


# =============================================================================
# PIPELINE A PARTIR DA SELEÇÃO FUNDAMENTAL
# =============================================================================

def get_robotics_market_data(
    fundamental_selection: pd.DataFrame,
    start: Optional[pd.Timestamp] = None,
    end: Optional[pd.Timestamp] = None,
) -> pd.DataFrame:
    """
    Entrada oficial do módulo.

    Recebe a seleção fundamental consolidada e baixa
    preços somente das empresas Robotics Top 5.
    """

    tickers = (
        extract_robotics_tickers(
            fundamental_selection
        )
    )

    price_history = (
        download_price_history(
            tickers=tickers,
            start=start,
            end=end,
        )
    )

    validate_market_data(
        price_history=price_history,
        expected_tickers=tickers,
    )

    return price_history


# =============================================================================
# VALIDAÇÃO
# =============================================================================

def validate_market_data(
    price_history: pd.DataFrame,
    expected_tickers: Optional[Iterable[str]] = None,
) -> bool:
    """
    Audita integridade do histórico.
    """

    if not isinstance(
        price_history,
        pd.DataFrame,
    ):
        raise TypeError(
            "price_history deve ser DataFrame."
        )

    if price_history.empty:
        raise AssertionError(
            "Histórico de preços vazio."
        )

    missing = (
        set(
            REQUIRED_OUTPUT_COLUMNS
        )
        - set(
            price_history.columns
        )
    )

    if missing:
        raise AssertionError(
            "Colunas obrigatórias ausentes: "
            f"{sorted(missing)}"
        )

    duplicates = (
        price_history
        .duplicated(
            subset=[
                "ticker",
                "date",
            ]
        )
    )

    if duplicates.any():
        raise AssertionError(
            "Datas duplicadas encontradas "
            "no Market Data."
        )

    if (
        price_history[
            "close"
        ]
        <= 0
    ).any():
        raise AssertionError(
            "Preço de fechamento inválido."
        )

    if (
        price_history[
            "high"
        ]
        < price_history[
            "low"
        ]
    ).any():
        raise AssertionError(
            "High inferior ao Low."
        )

    if expected_tickers is not None:

        expected = {
            normalize_ticker(
                ticker
            )
            for ticker in expected_tickers
        }

        actual = set(
            price_history[
                "ticker"
            ]
            .astype(str)
            .str.upper()
        )

        missing_tickers = (
            expected
            - actual
        )

        unexpected_tickers = (
            actual
            - expected
        )

        if missing_tickers:
            raise AssertionError(
                "Empresas Robotics sem preços: "
                f"{sorted(missing_tickers)}"
            )

        if unexpected_tickers:
            raise AssertionError(
                "Empresa não selecionada entrou "
                "no Market Data: "
                f"{sorted(unexpected_tickers)}"
            )

    return True


# =============================================================================
# ADICIONAR GICS REAL
# =============================================================================

def attach_real_gics(
    price_history: pd.DataFrame,
    fundamental_selection: pd.DataFrame,
) -> pd.DataFrame:
    """
    Adiciona setor e subindústria GICS reais.

    REGRA IMPORTANTE
    ----------------
    O AI Infrastructure Scanner original possui componentes
    relativos a setor.

    Portanto, NÃO utilizamos "ROBOTICS" como setor.

    O campo setor deve continuar representando o setor GICS
    verdadeiro da empresa.
    """

    required_selection = {
        "ticker",
        "gics_sector",
        "gics_sub_industry",
    }

    missing = (
        required_selection
        - set(
            fundamental_selection.columns
        )
    )

    if missing:
        raise ValueError(
            "Seleção fundamental sem GICS: "
            f"{sorted(missing)}"
        )

    metadata = (
        fundamental_selection[
            [
                "ticker",
                "gics_sector",
                "gics_sub_industry",
            ]
        ]
        .drop_duplicates(
            subset=[
                "ticker",
            ],
            keep="first",
        )
        .copy()
    )

    metadata[
        "ticker"
    ] = (
        metadata[
            "ticker"
        ]
        .astype(str)
        .str.upper()
    )

    result = (
        price_history
        .merge(
            metadata,
            on="ticker",
            how="left",
            validate="many_to_one",
        )
    )

    if result[
        "gics_sector"
    ].isna().any():

        missing_tickers = sorted(
            result.loc[
                result[
                    "gics_sector"
                ].isna(),
                "ticker",
            ]
            .unique()
            .tolist()
        )

        raise AssertionError(
            "GICS real ausente para: "
            f"{missing_tickers}"
        )

    # Nome esperado pelo scanner original.

    result[
        "setor"
    ] = (
        result[
            "gics_sector"
        ]
    )

    return result


# =============================================================================
# RESUMO
# =============================================================================

def market_data_summary(
    price_history: pd.DataFrame,
) -> pd.DataFrame:
    """
    Resume cobertura por ticker.
    """

    if price_history.empty:
        return pd.DataFrame()

    summary = (
        price_history
        .groupby(
            "ticker",
            as_index=False,
        )
        .agg(
            first_date=(
                "date",
                "min",
            ),
            last_date=(
                "date",
                "max",
            ),
            sessions=(
                "date",
                "count",
            ),
            last_close=(
                "close",
                "last",
            ),
        )
    )

    return summary


# =============================================================================
# EXIBIÇÃO
# =============================================================================

def print_market_data_summary(
    price_history: pd.DataFrame,
) -> None:
    """
    Exibe cobertura de Market Data.
    """

    summary = (
        market_data_summary(
            price_history
        )
    )

    print(
        "=" * 100
    )

    print(
        "ROBOTICS_QUANTUM_SP500 — "
        "ROBOTICS MARKET DATA"
    )

    print(
        "=" * 100
    )

    print(
        summary.to_string(
            index=False
        )
    )

    print(
        "\nEmpresas:"
        f" {summary['ticker'].nunique()}"
    )

    print(
        "Linhas:"
        f" {len(price_history)}"
    )
