"""
ROBOTICS_QUANTUM_SP500
======================

Coleta fundamental via SEC Company Facts.

OBJETIVO
--------
Produzir exatamente as métricas necessárias aos dois fatores
fundamentais congelados:

ROBOTICS — Financial Strength
    cash_assets
    debt_assets
    debt_equity

QUANTUM — Growth
    revenue_growth
    eps_growth
    operating_cash_flow_growth

PRINCÍPIOS
----------
- SEC Company Facts como fonte fundamental.
- Utilizar somente fatos publicados/disponíveis.
- Preservar a metodologia do robô fundamental original.
- Não calcular ranking neste módulo.
- Não utilizar preços.
- Não utilizar retornos futuros.
"""

from __future__ import annotations

import time
from typing import Dict, Iterable, List, Optional, Tuple

import numpy as np
import pandas as pd
import requests

from config.settings import (
    SEC_COMPANYFACTS_URL,
    SEC_USER_AGENT,
    FUNDAMENTAL_SNAPSHOT_FILE,
)


# =============================================================================
# HTTP
# =============================================================================

REQUEST_TIMEOUT = 30
REQUEST_SLEEP = 0.12

SEC_HEADERS = {
    "User-Agent": SEC_USER_AGENT,
    "Accept-Encoding": "gzip, deflate",
    "Accept": "application/json",
}


# =============================================================================
# TAGS SEC
# =============================================================================

TOTAL_ASSETS_TAGS = [
    "Assets",
]

CASH_TAGS = [
    "CashAndCashEquivalentsAtCarryingValue",
    "CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalents",
]

EQUITY_TAGS = [
    "StockholdersEquity",
    "StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest",
]


# -----------------------------------------------------------------------------
# Dívida
# -----------------------------------------------------------------------------
# Prioridade:
#
# 1. dívida total direta;
# 2. current + noncurrent;
# 3. finance lease;
# 4. operating lease;
#
# O fallback existe para evitar perda total da métrica quando a empresa
# não reporta um conceito direto de dívida.
# -----------------------------------------------------------------------------

TOTAL_DEBT_TAGS = [
    "LongTermDebtAndFinanceLeaseObligationsCurrent",
    "LongTermDebtAndFinanceLeaseObligations",
    "DebtCurrent",
    "DebtLongtermAndShorttermCombinedAmount",
]

CURRENT_DEBT_TAGS = [
    "ShortTermBorrowings",
    "ShortTermDebtCurrent",
    "LongTermDebtCurrent",
    "LongTermDebtAndFinanceLeaseObligationsCurrent",
]

NONCURRENT_DEBT_TAGS = [
    "LongTermDebtNoncurrent",
    "LongTermDebtAndFinanceLeaseObligationsNoncurrent",
]

FINANCE_LEASE_TAGS = [
    "FinanceLeaseLiability",
    "FinanceLeaseLiabilityCurrent",
    "FinanceLeaseLiabilityNoncurrent",
]

OPERATING_LEASE_TAGS = [
    "OperatingLeaseLiability",
    "OperatingLeaseLiabilityCurrent",
    "OperatingLeaseLiabilityNoncurrent",
]


# -----------------------------------------------------------------------------
# Growth
# -----------------------------------------------------------------------------

REVENUE_TAGS = [
    "RevenueFromContractWithCustomerExcludingAssessedTax",
    "SalesRevenueNet",
    "Revenues",
]

EPS_TAGS = [
    "EarningsPerShareDiluted",
]

OPERATING_CASH_FLOW_TAGS = [
    "NetCashProvidedByUsedInOperatingActivities",
]


# =============================================================================
# HELPERS
# =============================================================================

def _safe_float(value):
    try:
        value = float(value)
    except (TypeError, ValueError):
        return np.nan

    if not np.isfinite(value):
        return np.nan

    return value


def safe_divide(
    numerator,
    denominator,
):
    numerator = _safe_float(numerator)
    denominator = _safe_float(denominator)

    if (
        pd.isna(numerator)
        or pd.isna(denominator)
        or denominator == 0
    ):
        return np.nan

    return numerator / denominator


def safe_growth(
    current,
    previous,
):
    """
    Crescimento utilizado pelo estudo:

        current / previous - 1

    Retorna NaN quando não é possível calcular.
    """

    current = _safe_float(current)
    previous = _safe_float(previous)

    if (
        pd.isna(current)
        or pd.isna(previous)
        or previous == 0
    ):
        return np.nan

    return (
        current
        / previous
        - 1.0
    )


def normalize_cik(cik) -> str:
    """
    SEC utiliza CIK com 10 dígitos.
    """

    if pd.isna(cik):
        raise ValueError(
            "CIK ausente."
        )

    return str(
        int(cik)
    ).zfill(10)


# =============================================================================
# DOWNLOAD COMPANY FACTS
# =============================================================================

def download_companyfacts(
    cik,
) -> Dict:
    """
    Baixa Company Facts de uma empresa.
    """

    cik10 = normalize_cik(
        cik
    )

    url = SEC_COMPANYFACTS_URL.format(
        cik=cik10
    )

    response = requests.get(
        url,
        headers=SEC_HEADERS,
        timeout=REQUEST_TIMEOUT,
    )

    response.raise_for_status()

    data = response.json()

    if not isinstance(
        data,
        dict,
    ):
        raise RuntimeError(
            f"Resposta SEC inválida para CIK {cik10}."
        )

    return data


# =============================================================================
# EXTRAÇÃO DE UNIDADES
# =============================================================================

def _concept_units(
    companyfacts: Dict,
    tag: str,
) -> Dict:
    """
    Retorna unidades disponíveis de um conceito US-GAAP.
    """

    facts = (
        companyfacts
        .get("facts", {})
        .get("us-gaap", {})
    )

    concept = facts.get(
        tag
    )

    if not concept:
        return {}

    return concept.get(
        "units",
        {}
    )


def _records_for_tag(
    companyfacts: Dict,
    tag: str,
    preferred_units: Optional[Iterable[str]] = None,
) -> List[Dict]:
    """
    Retorna registros de um conceito SEC.

    preferred_units define prioridade de unidade.
    """

    units = _concept_units(
        companyfacts,
        tag,
    )

    if not units:
        return []

    if preferred_units:

        for unit in preferred_units:

            records = units.get(
                unit
            )

            if records:
                return list(
                    records
                )

    # fallback: primeira unidade disponível

    for records in units.values():

        if records:
            return list(
                records
            )

    return []


# =============================================================================
# FILTRO DE FATOS PUBLICADOS
# =============================================================================

def _prepare_records(
    records: List[Dict],
    as_of_date: Optional[pd.Timestamp] = None,
) -> pd.DataFrame:
    """
    Normaliza fatos SEC.

    Se as_of_date for informado, somente fatos publicados
    até aquela data são permitidos.
    """

    if not records:
        return pd.DataFrame()

    df = pd.DataFrame(
        records
    )

    if df.empty:
        return df

    for column in (
        "filed",
        "start",
        "end",
    ):

        if column in df.columns:

            df[column] = pd.to_datetime(
                df[column],
                errors="coerce",
            )

    if (
        as_of_date is not None
        and "filed" in df.columns
    ):

        cutoff = pd.Timestamp(
            as_of_date
        )

        df = df.loc[
            df["filed"] <= cutoff
        ].copy()

    if "val" in df.columns:

        df["val"] = pd.to_numeric(
            df["val"],
            errors="coerce",
        )

    return df


# =============================================================================
# FATOS INSTANTÂNEOS
# =============================================================================

def latest_instant_fact(
    companyfacts: Dict,
    tags: Iterable[str],
    as_of_date: Optional[pd.Timestamp] = None,
) -> Optional[Dict]:
    """
    Obtém o fato instantâneo mais recente disponível.
    """

    candidates = []

    for priority, tag in enumerate(
        tags
    ):

        records = _records_for_tag(
            companyfacts,
            tag,
            preferred_units=[
                "USD",
            ],
        )

        df = _prepare_records(
            records,
            as_of_date=as_of_date,
        )

        if df.empty:
            continue

        if "end" not in df.columns:
            continue

        df = df.loc[
            df["end"].notna()
            & df["val"].notna()
        ].copy()

        if df.empty:
            continue

        df["tag"] = tag
        df["priority"] = priority

        candidates.append(
            df
        )

    if not candidates:
        return None

    all_facts = pd.concat(
        candidates,
        ignore_index=True,
    )

    sort_columns = [
        "end",
    ]

    if "filed" in all_facts.columns:
        sort_columns.append(
            "filed"
        )

    all_facts = all_facts.sort_values(
        sort_columns
    )

    latest_end = all_facts[
        "end"
    ].max()

    latest = all_facts.loc[
        all_facts["end"]
        == latest_end
    ].copy()

    latest = latest.sort_values(
        "priority"
    )

    row = latest.iloc[0]

    return {
        "value":
            _safe_float(
                row["val"]
            ),

        "tag":
            row["tag"],

        "end":
            row["end"],

        "filed":
            row.get(
                "filed",
                pd.NaT,
            ),
    }


# =============================================================================
# FATOS ANUAIS
# =============================================================================

def _annual_records(
    companyfacts: Dict,
    tags: Iterable[str],
    preferred_units: Iterable[str],
    as_of_date: Optional[pd.Timestamp] = None,
) -> pd.DataFrame:
    """
    Constrói conjunto de fatos anuais disponíveis.

    Dá preferência a registros FY/10-K quando essas informações
    estiverem presentes.
    """

    candidates = []

    for priority, tag in enumerate(
        tags
    ):

        records = _records_for_tag(
            companyfacts,
            tag,
            preferred_units=preferred_units,
        )

        df = _prepare_records(
            records,
            as_of_date=as_of_date,
        )

        if df.empty:
            continue

        if (
            "start" not in df.columns
            or "end" not in df.columns
        ):
            continue

        df = df.loc[
            df["start"].notna()
            & df["end"].notna()
            & df["val"].notna()
        ].copy()

        if df.empty:
            continue

        # Duração ajuda a eliminar períodos trimestrais.

        df["duration_days"] = (
            df["end"]
            - df["start"]
        ).dt.days

        df = df.loc[
            df["duration_days"]
            .between(
                250,
                450,
            )
        ].copy()

        if df.empty:
            continue

        if "fp" in df.columns:

            annual_fp = df[
                "fp"
            ].isin(
                [
                    "FY",
                ]
            )

            if annual_fp.any():

                df = df.loc[
                    annual_fp
                ].copy()

        if "form" in df.columns:

            annual_form = df[
                "form"
            ].isin(
                [
                    "10-K",
                    "10-K/A",
                    "20-F",
                    "20-F/A",
                    "40-F",
                ]
            )

            if annual_form.any():

                df = df.loc[
                    annual_form
                ].copy()

        if df.empty:
            continue

        df["tag"] = tag
        df["priority"] = priority

        candidates.append(
            df
        )

    if not candidates:
        return pd.DataFrame()

    result = pd.concat(
        candidates,
        ignore_index=True,
    )

    return result


def last_two_annual_values(
    companyfacts: Dict,
    tags: Iterable[str],
    preferred_units: Iterable[str],
    as_of_date: Optional[pd.Timestamp] = None,
) -> Tuple[float, float]:
    """
    Retorna os dois últimos valores anuais distintos disponíveis.
    """

    df = _annual_records(
        companyfacts=companyfacts,
        tags=tags,
        preferred_units=preferred_units,
        as_of_date=as_of_date,
    )

    if df.empty:
        return (
            np.nan,
            np.nan,
        )

    # Escolher a tag de maior prioridade que possua
    # pelo menos dois períodos anuais.

    for priority in sorted(
        df["priority"].unique()
    ):

        subset = df.loc[
            df["priority"]
            == priority
        ].copy()

        if subset.empty:
            continue

        sort_columns = [
            "end",
        ]

        if "filed" in subset.columns:
            sort_columns.append(
                "filed"
            )

        subset = subset.sort_values(
            sort_columns
        )

        # Um mesmo período pode aparecer várias vezes
        # em filings posteriores.
        # Mantemos o último registro permitido para cada end.

        subset = subset.drop_duplicates(
            subset=["end"],
            keep="last",
        )

        subset = subset.sort_values(
            "end"
        )

        if len(subset) < 2:
            continue

        current = _safe_float(
            subset.iloc[-1][
                "val"
            ]
        )

        previous = _safe_float(
            subset.iloc[-2][
                "val"
            ]
        )

        return (
            current,
            previous,
        )

    return (
        np.nan,
        np.nan,
    )


# =============================================================================
# DÍVIDA
# =============================================================================

def _sum_latest_components(
    companyfacts: Dict,
    tags: Iterable[str],
    as_of_date: Optional[pd.Timestamp] = None,
) -> Optional[Dict]:
    """
    Soma componentes disponíveis referentes à mesma
    data de balanço mais recente.
    """

    components = []

    for tag in tags:

        fact = latest_instant_fact(
            companyfacts,
            [tag],
            as_of_date=as_of_date,
        )

        if fact is not None:
            components.append(
                fact
            )

    if not components:
        return None

    latest_end = max(
        component["end"]
        for component in components
    )

    same_period = [
        component
        for component in components
        if component["end"]
        == latest_end
    ]

    if not same_period:
        return None

    values = [
        component["value"]
        for component in same_period
        if pd.notna(
            component["value"]
        )
    ]

    if not values:
        return None

    return {
        "value":
            float(
                np.sum(values)
            ),

        "end":
            latest_end,

        "filed":
            max(
                [
                    component["filed"]
                    for component in same_period
                    if pd.notna(
                        component["filed"]
                    )
                ],
                default=pd.NaT,
            ),

        "tag":
            "+".join(
                component["tag"]
                for component in same_period
            ),
    }


def extract_debt(
    companyfacts: Dict,
    as_of_date: Optional[pd.Timestamp] = None,
) -> Optional[Dict]:
    """
    Hierarquia de dívida utilizada pelo projeto.
    """

    # 1. Conceito direto

    direct = latest_instant_fact(
        companyfacts,
        TOTAL_DEBT_TAGS,
        as_of_date=as_of_date,
    )

    if direct is not None:
        direct["source"] = (
            "DIRECT_DEBT"
        )
        return direct

    # 2. Dívida corrente + não corrente

    current = latest_instant_fact(
        companyfacts,
        CURRENT_DEBT_TAGS,
        as_of_date=as_of_date,
    )

    noncurrent = latest_instant_fact(
        companyfacts,
        NONCURRENT_DEBT_TAGS,
        as_of_date=as_of_date,
    )

    if (
        current is not None
        and noncurrent is not None
        and current["end"]
        == noncurrent["end"]
    ):

        return {
            "value":
                current["value"]
                + noncurrent["value"],

            "end":
                current["end"],

            "filed":
                max(
                    current["filed"],
                    noncurrent["filed"],
                ),

            "tag":
                (
                    f"{current['tag']}"
                    "+"
                    f"{noncurrent['tag']}"
                ),

            "source":
                "CURRENT_PLUS_NONCURRENT",
        }

    # 3. Finance lease

    finance = _sum_latest_components(
        companyfacts,
        FINANCE_LEASE_TAGS,
        as_of_date=as_of_date,
    )

    if finance is not None:
        finance["source"] = (
            "FINANCE_LEASE_FALLBACK"
        )
        return finance

    # 4. Operating lease

    operating = _sum_latest_components(
        companyfacts,
        OPERATING_LEASE_TAGS,
        as_of_date=as_of_date,
    )

    if operating is not None:
        operating["source"] = (
            "OPERATING_LEASE_FALLBACK"
        )
        return operating

    return None


# =============================================================================
# MÉTRICAS DE UMA EMPRESA
# =============================================================================

def calculate_company_metrics(
    companyfacts: Dict,
    as_of_date: Optional[pd.Timestamp] = None,
) -> Dict:
    """
    Calcula somente as seis métricas utilizadas
    pela política fundamental congelada.
    """

    assets_fact = latest_instant_fact(
        companyfacts,
        TOTAL_ASSETS_TAGS,
        as_of_date=as_of_date,
    )

    cash_fact = latest_instant_fact(
        companyfacts,
        CASH_TAGS,
        as_of_date=as_of_date,
    )

    equity_fact = latest_instant_fact(
        companyfacts,
        EQUITY_TAGS,
        as_of_date=as_of_date,
    )

    debt_fact = extract_debt(
        companyfacts,
        as_of_date=as_of_date,
    )

    assets = (
        assets_fact["value"]
        if assets_fact
        else np.nan
    )

    cash = (
        cash_fact["value"]
        if cash_fact
        else np.nan
    )

    equity = (
        equity_fact["value"]
        if equity_fact
        else np.nan
    )

    debt = (
        debt_fact["value"]
        if debt_fact
        else np.nan
    )

    cash_assets = safe_divide(
        cash,
        assets,
    )

    debt_assets = safe_divide(
        debt,
        assets,
    )

    debt_equity = safe_divide(
        debt,
        equity,
    )

    revenue_current, revenue_previous = (
        last_two_annual_values(
            companyfacts,
            REVENUE_TAGS,
            preferred_units=[
                "USD",
            ],
            as_of_date=as_of_date,
        )
    )

    eps_current, eps_previous = (
        last_two_annual_values(
            companyfacts,
            EPS_TAGS,
            preferred_units=[
                "USD/shares",
                "USD / shares",
            ],
            as_of_date=as_of_date,
        )
    )

    ocf_current, ocf_previous = (
        last_two_annual_values(
            companyfacts,
            OPERATING_CASH_FLOW_TAGS,
            preferred_units=[
                "USD",
            ],
            as_of_date=as_of_date,
        )
    )

    revenue_growth = safe_growth(
        revenue_current,
        revenue_previous,
    )

    eps_growth = safe_growth(
        eps_current,
        eps_previous,
    )

    operating_cash_flow_growth = (
        safe_growth(
            ocf_current,
            ocf_previous,
        )
    )

    return {
        "cash_assets":
            cash_assets,

        "debt_assets":
            debt_assets,

        "debt_equity":
            debt_equity,

        "revenue_growth":
            revenue_growth,

        "eps_growth":
            eps_growth,

        "operating_cash_flow_growth":
            operating_cash_flow_growth,

        "total_assets":
            assets,

        "cash":
            cash,

        "total_debt":
            debt,

        "equity":
            equity,

        "debt_source":
            (
                debt_fact.get(
                    "source"
                )
                if debt_fact
                else None
            ),

        "assets_tag":
            (
                assets_fact.get(
                    "tag"
                )
                if assets_fact
                else None
            ),

        "cash_tag":
            (
                cash_fact.get(
                    "tag"
                )
                if cash_fact
                else None
            ),

        "equity_tag":
            (
                equity_fact.get(
                    "tag"
                )
                if equity_fact
                else None
            ),
    }


# =============================================================================
# SNAPSHOT DO UNIVERSO
# =============================================================================

def build_fundamental_snapshot(
    universe: pd.DataFrame,
    as_of_date: Optional[pd.Timestamp] = None,
    save: bool = True,
) -> pd.DataFrame:
    """
    Coleta fundamentos de todas as empresas do universo.

    universe deve conter:
        ticker
        company
        cik
        theme
        exposure
        gics_sector
        gics_sub_industry
    """

    required = {
        "ticker",
        "company",
        "cik",
        "theme",
        "exposure",
        "gics_sector",
        "gics_sub_industry",
    }

    missing = (
        required
        - set(universe.columns)
    )

    if missing:
        raise ValueError(
            "Colunas ausentes no universo fundamental: "
            f"{sorted(missing)}"
        )

    if universe.empty:
        raise ValueError(
            "Universo fundamental vazio."
        )

    rows = []

    errors = []

    total = len(
        universe
    )

    for position, row in enumerate(
        universe.itertuples(
            index=False
        ),
        start=1,
    ):

        ticker = str(
            row.ticker
        ).upper()

        print(
            f"[{position:02d}/{total:02d}] "
            f"SEC fundamentals: {ticker}"
        )

        try:

            companyfacts = (
                download_companyfacts(
                    row.cik
                )
            )

            metrics = (
                calculate_company_metrics(
                    companyfacts,
                    as_of_date=as_of_date,
                )
            )

            output = {
                "ticker":
                    ticker,

                "company":
                    row.company,

                "cik":
                    row.cik,

                "theme":
                    row.theme,

                "exposure":
                    row.exposure,

                "gics_sector":
                    row.gics_sector,

                "gics_sub_industry":
                    row.gics_sub_industry,

                "snapshot_date":
                    (
                        pd.Timestamp(
                            as_of_date
                        )
                        if as_of_date
                        is not None
                        else pd.Timestamp.utcnow()
                    ),
            }

            output.update(
                metrics
            )

            rows.append(
                output
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
                f"   ERRO: {exc}"
            )

        time.sleep(
            REQUEST_SLEEP
        )

    result = pd.DataFrame(
        rows
    )

    if result.empty:
        raise RuntimeError(
            "Nenhum fundamento foi coletado."
        )

    metric_columns = [
        "cash_assets",
        "debt_assets",
        "debt_equity",
        "revenue_growth",
        "eps_growth",
        "operating_cash_flow_growth",
    ]

    for column in metric_columns:

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

    # -------------------------------------------------------------------------
    # Cobertura dos dois fatores
    # -------------------------------------------------------------------------

    result[
        "financial_strength_components"
    ] = (
        result[
            [
                "cash_assets",
                "debt_assets",
                "debt_equity",
            ]
        ]
        .notna()
        .sum(axis=1)
    )

    result[
        "growth_components"
    ] = (
        result[
            [
                "revenue_growth",
                "eps_growth",
                "operating_cash_flow_growth",
            ]
        ]
        .notna()
        .sum(axis=1)
    )

    result[
        "financial_strength_eligible"
    ] = (
        result[
            "financial_strength_components"
        ]
        >= 2
    )

    result[
        "growth_eligible"
    ] = (
        result[
            "growth_components"
        ]
        >= 2
    )

    result = (
        result
        .sort_values(
            "ticker"
        )
        .reset_index(
            drop=True
        )
    )

    if save:

        FUNDAMENTAL_SNAPSHOT_FILE.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        result.to_csv(
            FUNDAMENTAL_SNAPSHOT_FILE,
            index=False,
        )

    if errors:

        print(
            "\nEmpresas com erro SEC:"
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
# AUDITORIA
# =============================================================================

def validate_fundamental_snapshot(
    snapshot: pd.DataFrame,
) -> bool:
    """
    Valida integridade mínima do snapshot fundamental.
    """

    required = {
        "ticker",
        "cash_assets",
        "debt_assets",
        "debt_equity",
        "revenue_growth",
        "eps_growth",
        "operating_cash_flow_growth",
        "financial_strength_components",
        "growth_components",
    }

    missing = (
        required
        - set(snapshot.columns)
    )

    if missing:
        raise AssertionError(
            "Snapshot fundamental incompleto: "
            f"{sorted(missing)}"
        )

    if snapshot.empty:
        raise AssertionError(
            "Snapshot fundamental vazio."
        )

    if snapshot[
        "ticker"
    ].duplicated().any():

        raise AssertionError(
            "Ticker duplicado no snapshot fundamental."
        )

    return True
