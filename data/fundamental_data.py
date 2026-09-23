# ======================================================================================
# ROBOTICS_QUANTUM_SP500
# data/fundamental_data.py
# ======================================================================================
#
# RESPONSABILIDADE
# ---------------
# Coletar e preparar os fundamentos utilizados pelo motor de seleção:
#
# ROBOTICS
#   Financial Strength
#       cash_assets ↑
#       debt_assets ↓
#       debt_equity ↓
#
# QUANTUM
#   Growth
#       revenue_growth ↑
#       eps_growth ↑
#       operating_cash_flow_growth ↑
#
# PRINCÍPIO
# ---------
# A metodologia fundamental reproduz a camada de dados do
# PORTFOLIO ACOES AMERICANO.
#
# Este módulo:
#   • NÃO seleciona empresas;
#   • NÃO calcula ranking;
#   • NÃO executa timing;
#   • NÃO gera venda.
#
# ======================================================================================

from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Dict, Iterable

import numpy as np
import pandas as pd
import requests

from config.settings import (
    CACHE_DIR,
    DATA_DIR,
    SEC_COMPANY_FACTS_URL,
    SEC_USER_AGENT,
)


# ======================================================================================
# 1. DIRETÓRIOS
# ======================================================================================

DATA_PATH = Path(DATA_DIR)
CACHE_PATH = Path(CACHE_DIR)

DATA_PATH.mkdir(
    parents=True,
    exist_ok=True,
)

CACHE_PATH.mkdir(
    parents=True,
    exist_ok=True,
)

FUNDAMENTAL_SNAPSHOT_FILE = (
    DATA_PATH
    / "fundamental_snapshot.csv"
)


# ======================================================================================
# 2. HTTP
# ======================================================================================

DECLARED_SEC_USER_AGENT = os.getenv(
    "SEC_USER_AGENT",
    SEC_USER_AGENT,
).strip()

SESSION = requests.Session()

SESSION.headers.update(
    {
        "User-Agent": DECLARED_SEC_USER_AGENT,
        "Accept-Encoding": "gzip, deflate",
        "Accept": "application/json,text/plain,*/*",
        "Connection": "keep-alive",
    }
)


# ======================================================================================
# 3. HELPERS
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


def safe_numeric(
    value,
):

    try:

        value = float(value)

        if np.isfinite(value):
            return value

    except Exception:
        pass

    return np.nan


def safe_growth(
    current,
    previous,
):

    current = safe_numeric(current)
    previous = safe_numeric(previous)

    if (
        not np.isfinite(current)
        or
        not np.isfinite(previous)
        or
        previous == 0
    ):
        return np.nan

    result = (
        current
        /
        previous
        -
        1.0
    )

    if np.isfinite(result):
        return result

    return np.nan


# ======================================================================================
# 4. DOWNLOAD JSON
# ======================================================================================

def request_json(
    url: str,
    retries: int = 4,
    sleep_seconds: float = 0.75,
):

    last_error = None

    for attempt in range(retries):

        try:

            response = SESSION.get(
                url,
                headers={
                    "User-Agent":
                        DECLARED_SEC_USER_AGENT,
                    "Accept-Encoding":
                        "gzip, deflate",
                    "Accept":
                        "application/json,text/plain,*/*",
                },
                timeout=30,
            )

            if response.status_code in (
                403,
                429,
            ):

                last_error = RuntimeError(
                    f"HTTP {response.status_code} "
                    f"para {url}"
                )

                time.sleep(
                    max(
                        2.0,
                        sleep_seconds
                        *
                        (attempt + 1)
                        *
                        2,
                    )
                )

                continue

            response.raise_for_status()

            return response.json()

        except Exception as exc:

            last_error = exc

            if attempt < retries - 1:

                time.sleep(
                    sleep_seconds
                    *
                    (attempt + 1)
                )

    raise RuntimeError(
        f"Falha ao acessar {url}: "
        f"{last_error}"
    )


# ======================================================================================
# 5. SEC COMPANY FACTS
# ======================================================================================

def get_company_facts(
    cik: str,
    use_cache: bool = True,
) -> Dict:

    cik = str(cik).zfill(10)

    cache_file = (
        CACHE_PATH
        /
        f"companyfacts_{cik}.json"
    )

    if (
        use_cache
        and
        cache_file.exists()
    ):

        try:

            cache_age_seconds = (
                time.time()
                -
                cache_file.stat().st_mtime
            )

            if (
                cache_age_seconds
                <
                24 * 60 * 60
            ):

                with open(
                    cache_file,
                    "r",
                    encoding="utf-8",
                ) as file:

                    return json.load(file)

        except Exception:
            pass

    url = (
        f"{SEC_COMPANY_FACTS_URL}"
        f"CIK{cik}.json"
    )

    data = request_json(url)

    with open(
        cache_file,
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            data,
            file,
        )

    time.sleep(0.20)

    return data


# ======================================================================================
# 6. CONCEITOS SEC
# ======================================================================================
#
# Os conceitos abaixo reproduzem os conceitos utilizados pelo
# PORTFOLIO ACOES AMERICANO para os fatores necessários ao novo robô.
#
# ======================================================================================

SEC_CONCEPTS = {

    "revenue": [
        (
            "us-gaap",
            "RevenueFromContractWithCustomerExcludingAssessedTax",
            "USD",
        ),
        (
            "us-gaap",
            "Revenues",
            "USD",
        ),
        (
            "us-gaap",
            "SalesRevenueNet",
            "USD",
        ),
    ],

    "operating_cash_flow": [
        (
            "us-gaap",
            "NetCashProvidedByUsedInOperatingActivities",
            "USD",
        ),
    ],

    "assets": [
        (
            "us-gaap",
            "Assets",
            "USD",
        ),
    ],

    "equity": [
        (
            "us-gaap",
            "StockholdersEquity",
            "USD",
        ),
        (
            "us-gaap",
            "StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest",
            "USD",
        ),
    ],

    "cash": [
        (
            "us-gaap",
            "CashAndCashEquivalentsAtCarryingValue",
            "USD",
        ),
        (
            "us-gaap",
            "CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalents",
            "USD",
        ),
    ],

    "long_term_debt": [
        (
            "us-gaap",
            "LongTermDebtNoncurrent",
            "USD",
        ),
        (
            "us-gaap",
            "LongTermDebt",
            "USD",
        ),
    ],

    "short_term_debt": [
        (
            "us-gaap",
            "ShortTermBorrowings",
            "USD",
        ),
        (
            "us-gaap",
            "ShortTermDebtCurrent",
            "USD",
        ),
        (
            "us-gaap",
            "LongTermDebtCurrent",
            "USD",
        ),
        (
            "us-gaap",
            "CurrentPortionOfLongTermDebt",
            "USD",
        ),
    ],

    "diluted_eps": [
        (
            "us-gaap",
            "EarningsPerShareDiluted",
            "USD/shares",
        ),
    ],
}


# ======================================================================================
# 7. EXTRAÇÃO DAS OBSERVAÇÕES SEC
# ======================================================================================

def extract_concept_observations(
    company_facts: Dict,
    concept_names: Iterable,
    ticker: str,
    metric_name: str,
) -> pd.DataFrame:

    rows = []

    for priority, spec in enumerate(
        concept_names
    ):

        taxonomy, tag, expected_unit = spec

        tag_data = (
            company_facts
            .get("facts", {})
            .get(taxonomy, {})
            .get(tag)
        )

        if tag_data is None:
            continue

        units = tag_data.get(
            "units",
            {},
        )

        observations = units.get(
            expected_unit
        )

        if observations is None:
            continue

        for obs in observations:

            value = safe_numeric(
                obs.get("val")
            )

            filed = pd.to_datetime(
                obs.get("filed"),
                errors="coerce",
            )

            end = pd.to_datetime(
                obs.get("end"),
                errors="coerce",
            )

            start = pd.to_datetime(
                obs.get("start"),
                errors="coerce",
            )

            if (
                pd.isna(filed)
                or
                pd.isna(end)
                or
                pd.isna(value)
            ):
                continue

            rows.append(
                {
                    "ticker":
                        normalize_ticker(
                            ticker
                        ),

                    "metric":
                        metric_name,

                    "concept":
                        tag,

                    "tag":
                        tag,

                    "priority":
                        int(priority),

                    "taxonomy":
                        taxonomy,

                    "unit":
                        expected_unit,

                    "value":
                        value,

                    "start":
                        start,

                    "end":
                        end,

                    "filed":
                        filed,

                    # REGRA ANTI-LOOK-AHEAD
                    "available_date":
                        filed,

                    "form":
                        obs.get("form"),

                    "fy":
                        obs.get("fy"),

                    "fp":
                        obs.get("fp"),

                    "accn":
                        obs.get("accn"),
                }
            )

    if not rows:
        return pd.DataFrame()

    df = pd.DataFrame(rows)

    valid_forms = {
        "10-K",
        "10-K/A",
        "10-Q",
        "10-Q/A",
        "20-F",
        "20-F/A",
        "40-F",
        "40-F/A",
    }

    df = df[
        df["form"].isin(
            valid_forms
        )
    ].copy()

    if df.empty:
        return pd.DataFrame()

    df = (
        df
        .sort_values(
            [
                "available_date",
                "end",
                "priority",
            ],
            ascending=[
                True,
                True,
                True,
            ],
        )
        .drop_duplicates(
            subset=[
                "ticker",
                "metric",
                "taxonomy",
                "tag",
                "end",
                "filed",
                "value",
            ],
            keep="last",
        )
        .reset_index(
            drop=True
        )
    )

    return df


# ======================================================================================
# 8. FUNDAMENTOS DE UMA EMPRESA
# ======================================================================================

def extract_company_fundamentals(
    ticker: str,
    cik: str,
    use_cache: bool = True,
) -> pd.DataFrame:

    company_facts = (
        get_company_facts(
            cik=cik,
            use_cache=use_cache,
        )
    )

    parts = []

    for (
        metric_name,
        concepts,
    ) in SEC_CONCEPTS.items():

        temp = (
            extract_concept_observations(
                company_facts=
                    company_facts,
                concept_names=
                    concepts,
                ticker=
                    ticker,
                metric_name=
                    metric_name,
            )
        )

        if not temp.empty:

            parts.append(
                temp
            )

    if not parts:
        return pd.DataFrame()

    return pd.concat(
        parts,
        ignore_index=True,
    )


# ======================================================================================
# 9. FUNDAMENTOS DO UNIVERSO TEMÁTICO
# ======================================================================================

def download_fundamentals(
    universe: pd.DataFrame,
    use_cache: bool = True,
):

    required = {
        "ticker",
        "cik",
    }

    if not required.issubset(
        universe.columns
    ):

        raise ValueError(
            "Universo precisa conter "
            "'ticker' e 'cik'."
        )

    parts = []
    errors = []

    total = len(universe)

    for number, row in enumerate(
        universe.itertuples(
            index=False
        ),
        start=1,
    ):

        ticker = normalize_ticker(
            row.ticker
        )

        cik = str(
            row.cik
        ).zfill(10)

        print(
            f"[{number:02d}/{total:02d}] "
            f"{ticker:<7}",
            end=" ",
        )

        try:

            temp = (
                extract_company_fundamentals(
                    ticker=ticker,
                    cik=cik,
                    use_cache=use_cache,
                )
            )

            if temp.empty:

                print("SEM DADOS")

                errors.append(
                    {
                        "ticker":
                            ticker,
                        "reason":
                            "SEM DADOS",
                    }
                )

                continue

            parts.append(
                temp
            )

            print(
                f"OK ({len(temp):,})"
            )

        except Exception as exc:

            print("ERRO")

            errors.append(
                {
                    "ticker":
                        ticker,
                    "reason":
                        str(exc),
                }
            )

    fundamentals = (
        pd.concat(
            parts,
            ignore_index=True,
        )
        if parts
        else
        pd.DataFrame()
    )

    errors_df = pd.DataFrame(
        errors
    )

    return (
        fundamentals,
        errors_df,
    )


# ======================================================================================
# 10. ÚLTIMA OBSERVAÇÃO CONHECIDA
# ======================================================================================

def _latest_metric_observation(
    df: pd.DataFrame,
) -> pd.Series:

    ordered = (
        df
        .sort_values(
            [
                "available_date",
                "end",
                "filed",
            ]
        )
    )

    return ordered.iloc[-1]


# ======================================================================================
# 11. GROWTH YoY POINT-IN-TIME
# ======================================================================================
#
# Reprodução da metodologia oficial:
#
#   1. available_date <= as_of_date
#   2. pega observação mais recente conhecida
#   3. procura observação aproximadamente um ano anterior
#   4. janela aceita: 300 a 430 dias
#   5. escolhe observação mais próxima de 365 dias
#   6. growth = current / previous - 1
#
# ======================================================================================

def calculate_point_in_time_growth(
    metric_history: pd.DataFrame,
    as_of_date,
) -> float:

    if metric_history.empty:
        return np.nan

    df = metric_history.copy()

    df["available_date"] = (
        pd.to_datetime(
            df["available_date"],
            errors="coerce",
        )
    )

    df["end"] = (
        pd.to_datetime(
            df["end"],
            errors="coerce",
        )
    )

    as_of_date = pd.Timestamp(
        as_of_date
    )

    df = df[
        df["available_date"]
        <=
        as_of_date
    ].copy()

    df = df[
        df["end"].notna()
        &
        df["value"].notna()
    ].copy()

    if len(df) < 2:
        return np.nan

    current = (
        _latest_metric_observation(
            df
        )
    )

    current_end = pd.Timestamp(
        current["end"]
    )

    candidates = df[
        df["end"]
        <
        current_end
    ].copy()

    if candidates.empty:
        return np.nan

    candidates[
        "days_difference"
    ] = (
        current_end
        -
        candidates["end"]
    ).dt.days

    candidates = candidates[
        candidates[
            "days_difference"
        ].between(
            300,
            430,
        )
    ].copy()

    if candidates.empty:
        return np.nan

    candidates[
        "distance_to_year"
    ] = (
        candidates[
            "days_difference"
        ]
        -
        365
    ).abs()

    candidates = (
        candidates
        .sort_values(
            [
                "distance_to_year",
                "available_date",
            ],
            ascending=[
                True,
                False,
            ],
        )
    )

    previous = candidates.iloc[0]

    return safe_growth(
        current["value"],
        previous["value"],
    )


# ======================================================================================
# 12. SNAPSHOT FUNDAMENTAL POINT-IN-TIME
# ======================================================================================

def latest_fundamental_snapshot(
    fundamentals: pd.DataFrame,
    as_of_date=None,
) -> pd.DataFrame:

    if fundamentals.empty:
        return pd.DataFrame()

    df = fundamentals.copy()

    df["available_date"] = (
        pd.to_datetime(
            df["available_date"],
            errors="coerce",
        )
    )

    df["filed"] = (
        pd.to_datetime(
            df["filed"],
            errors="coerce",
        )
    )

    df["end"] = (
        pd.to_datetime(
            df["end"],
            errors="coerce",
        )
    )

    if as_of_date is None:

        as_of_date = (
            pd.Timestamp.today()
            .normalize()
        )

    else:

        as_of_date = pd.Timestamp(
            as_of_date
        )

    # ------------------------------------------------------------------
    # ANTI-LOOK-AHEAD
    # ------------------------------------------------------------------

    known = df[
        (
            df["available_date"]
            <=
            as_of_date
        )
        &
        (
            df["end"]
            <=
            as_of_date
        )
    ].copy()

    if known.empty:
        return pd.DataFrame()

    # ------------------------------------------------------------------
    # ÚLTIMO FATO CONHECIDO POR TICKER/MÉTRICA
    # ------------------------------------------------------------------

    latest = (
        known
        .sort_values(
            [
                "ticker",
                "metric",
                "available_date",
                "end",
            ]
        )
        .groupby(
            [
                "ticker",
                "metric",
            ],
            as_index=False,
        )
        .tail(1)
    )

    wide = (
        latest
        .pivot(
            index="ticker",
            columns="metric",
            values="value",
        )
        .reset_index()
    )

    wide.columns.name = None

    # ------------------------------------------------------------------
    # GROWTH
    # ------------------------------------------------------------------

    growth_metrics = {
        "revenue":
            "revenue_growth",

        "diluted_eps":
            "eps_growth",

        "operating_cash_flow":
            "operating_cash_flow_growth",
    }

    growth_rows = []

    for ticker in (
        wide["ticker"].unique()
    ):

        ticker_history = known[
            known["ticker"]
            ==
            ticker
        ]

        row = {
            "ticker":
                ticker,
        }

        for (
            raw_metric,
            output_metric,
        ) in growth_metrics.items():

            history = ticker_history[
                ticker_history["metric"]
                ==
                raw_metric
            ]

            row[
                output_metric
            ] = (
                calculate_point_in_time_growth(
                    metric_history=
                        history,
                    as_of_date=
                        as_of_date,
                )
            )

        growth_rows.append(
            row
        )

    growth_df = pd.DataFrame(
        growth_rows
    )

    wide = wide.merge(
        growth_df,
        on="ticker",
        how="left",
    )

    # ------------------------------------------------------------------
    # GARANTIR COLUNAS NECESSÁRIAS
    # ------------------------------------------------------------------

    required_numeric = [
        "revenue",
        "operating_cash_flow",
        "assets",
        "equity",
        "cash",
        "long_term_debt",
        "short_term_debt",
        "diluted_eps",
    ]

    for column in required_numeric:

        if column not in wide.columns:
            wide[column] = np.nan

        wide[column] = (
            pd.to_numeric(
                wide[column],
                errors="coerce",
            )
        )

    # ------------------------------------------------------------------
    # DÍVIDA TOTAL
    #
    # METODOLOGIA OFICIAL:
    #
    #   long_term_debt
    #       +
    #   short_term_debt
    #
    # NÃO são adicionados:
    #   • finance lease
    #   • operating lease
    #   • debt tags alternativos fora da base original
    # ------------------------------------------------------------------

    debt_components = (
        wide[
            "long_term_debt"
        ].fillna(0)
        +
        wide[
            "short_term_debt"
        ].fillna(0)
    )

    no_debt_data = (
        wide[
            "long_term_debt"
        ].isna()
        &
        wide[
            "short_term_debt"
        ].isna()
    )

    debt_components.loc[
        no_debt_data
    ] = np.nan

    wide[
        "total_debt"
    ] = debt_components

    # ------------------------------------------------------------------
    # RATIOS
    # ------------------------------------------------------------------

    def divide_columns(
        numerator: str,
        denominator: str,
    ) -> pd.Series:

        result = (
            wide[numerator]
            /
            wide[
                denominator
            ].replace(
                0,
                np.nan,
            )
        )

        return result.replace(
            [
                np.inf,
                -np.inf,
            ],
            np.nan,
        )

    # Financial Strength

    wide[
        "cash_assets"
    ] = divide_columns(
        "cash",
        "assets",
    )

    wide[
        "debt_assets"
    ] = divide_columns(
        "total_debt",
        "assets",
    )

    wide[
        "debt_equity"
    ] = divide_columns(
        "total_debt",
        "equity",
    )

    # ------------------------------------------------------------------
    # LIMPEZA
    # ------------------------------------------------------------------

    factor_columns = [
        "cash_assets",
        "debt_assets",
        "debt_equity",
        "revenue_growth",
        "eps_growth",
        "operating_cash_flow_growth",
    ]

    for column in factor_columns:

        if column not in wide.columns:
            wide[column] = np.nan

        wide[column] = (
            pd.to_numeric(
                wide[column],
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
        wide
        .sort_values(
            "ticker"
        )
        .reset_index(
            drop=True
        )
    )


# ======================================================================================
# 13. PREPARAR SNAPSHOT DO UNIVERSO TEMÁTICO
# ======================================================================================

def prepare_selection_snapshot(
    universe: pd.DataFrame,
    fundamentals: pd.DataFrame,
    as_of_date=None,
) -> pd.DataFrame:

    if "ticker" not in universe.columns:

        raise ValueError(
            "Universo precisa conter "
            "a coluna 'ticker'."
        )

    snapshot = (
        latest_fundamental_snapshot(
            fundamentals=
                fundamentals,
            as_of_date=
                as_of_date,
        )
    )

    if snapshot.empty:

        raise RuntimeError(
            "Snapshot fundamental "
            "retornou vazio."
        )

    base = universe.copy()

    base["ticker"] = (
        base["ticker"]
        .map(
            normalize_ticker
        )
    )

    result = base.merge(
        snapshot,
        on="ticker",
        how="inner",
    )

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
# 14. AUDITORIA DE LOOK-AHEAD
# ======================================================================================

def audit_lookahead(
    fundamentals: pd.DataFrame,
) -> int:

    if fundamentals.empty:
        return 0

    available = pd.to_datetime(
        fundamentals[
            "available_date"
        ],
        errors="coerce",
    )

    filed = pd.to_datetime(
        fundamentals[
            "filed"
        ],
        errors="coerce",
    )

    invalid = (
        available
        <
        filed
    )

    return int(
        invalid
        .fillna(False)
        .sum()
    )


# ======================================================================================
# 15. AUDITORIA DE COBERTURA
# ======================================================================================

def audit_selection_snapshot(
    snapshot: pd.DataFrame,
) -> pd.DataFrame:

    metrics = [
        "cash_assets",
        "debt_assets",
        "debt_equity",
        "revenue_growth",
        "eps_growth",
        "operating_cash_flow_growth",
    ]

    rows = []

    total = len(snapshot)

    for metric in metrics:

        if metric in snapshot.columns:

            available = int(
                snapshot[
                    metric
                ]
                .notna()
                .sum()
            )

        else:

            available = 0

        rows.append(
            {
                "metric":
                    metric,

                "available":
                    available,

                "total":
                    total,

                "coverage":
                    (
                        available
                        /
                        total
                        if total
                        else
                        np.nan
                    ),
            }
        )

    return pd.DataFrame(
        rows
    )


# ======================================================================================
# 16. FACHADA DO MÓDULO
# ======================================================================================

class FundamentalData:

    @staticmethod
    def calculate(
        universe: pd.DataFrame,
        as_of_date=None,
        use_cache: bool = True,
        save: bool = True,
    ) -> pd.DataFrame:

        if universe is None or universe.empty:

            raise ValueError(
                "Universo temático vazio."
            )

        fundamentals, errors = (
            download_fundamentals(
                universe=
                    universe,
                use_cache=
                    use_cache,
            )
        )

        if fundamentals.empty:

            raise RuntimeError(
                "Nenhum fundamento "
                "foi coletado."
            )

        snapshot = (
            prepare_selection_snapshot(
                universe=
                    universe,
                fundamentals=
                    fundamentals,
                as_of_date=
                    as_of_date,
            )
        )

        if snapshot.empty:

            raise RuntimeError(
                "Snapshot fundamental "
                "final vazio."
            )

        lookahead_violations = (
            audit_lookahead(
                fundamentals
            )
        )

        if lookahead_violations != 0:

            raise RuntimeError(
                "Violação de look-ahead "
                f"detectada: "
                f"{lookahead_violations}"
            )

        if save:

            FUNDAMENTAL_SNAPSHOT_FILE.parent.mkdir(
                parents=True,
                exist_ok=True,
            )

            snapshot.to_csv(
                FUNDAMENTAL_SNAPSHOT_FILE,
                index=False,
            )

            if not errors.empty:

                errors.to_csv(
                    DATA_PATH
                    /
                    "fundamental_errors.csv",
                    index=False,
                )

        return snapshot


# ======================================================================================
# 17. TESTE DIRETO
# ======================================================================================

if __name__ == "__main__":

    print(
        "=" * 100
    )

    print(
        "ROBOTICS_QUANTUM_SP500 "
        "— FUNDAMENTAL DATA"
    )

    print(
        "=" * 100
    )

    print(
        "\nMetodologia fundamental:"
    )

    print(
        "  ROBOTICS:"
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
        "\n  QUANTUM:"
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
        "\nPoint-in-time:"
    )

    print(
        "  available_date = filed"
    )

    print(
        "  crescimento YoY = "
        "comparação 300–430 dias"
    )

    print(
        "\nFundamental data layer "
        "carregada com sucesso."
    )
