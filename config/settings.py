"""
ROBOTICS_QUANTUM_SP500
======================

Configuração central do robô.

ARQUITETURA CONGELADA PELO ESTUDO:

S&P 500
    ↓
Robotics / Quantum
    ↓
Seleção Fundamental
    ↓
ROBOTICS:
    Financial Strength -> Top 5
    -> AI Infrastructure Signal Engine para timing de entrada

QUANTUM:
    Growth -> Top 2
    -> Fundamental puro

REGRAS INVIOLÁVEIS:
- Timing não altera seleção fundamental.
- Timing não altera ranking fundamental.
- Timing não gera venda.
- Empresa sai quando deixa de pertencer à seleção fundamental.
- Não permitir look-ahead.
"""

from pathlib import Path


# =============================================================================
# PROJETO
# =============================================================================

PROJECT_NAME = "ROBOTICS_QUANTUM_SP500"
PROJECT_VERSION = "1.0.0"

BASE_DIR = Path(__file__).resolve().parent.parent

DATA_DIR = BASE_DIR / "data"
REPORTS_DIR = BASE_DIR / "reports"
OUTPUT_DIR = BASE_DIR / "output"
CACHE_DIR = BASE_DIR / "cache"


# =============================================================================
# UNIVERSO
# =============================================================================

UNIVERSE_NAME = "S&P 500"

REQUIRE_SP500_MEMBERSHIP = True

ALLOWED_THEMES = (
    "ROBOTICS",
    "QUANTUM",
    "BOTH",
)


# =============================================================================
# POLÍTICA FUNDAMENTAL — ROBOTICS
# =============================================================================

ROBOTICS_FACTOR = "FINANCIAL_STRENGTH"

ROBOTICS_TOP_N = 5

ROBOTICS_MIN_COMPONENTS = 2

ROBOTICS_FINANCIAL_STRENGTH_HIGHER_IS_BETTER = (
    "cash_assets",
)

ROBOTICS_FINANCIAL_STRENGTH_LOWER_IS_BETTER = (
    "debt_assets",
    "debt_equity",
)


# =============================================================================
# POLÍTICA FUNDAMENTAL — QUANTUM
# =============================================================================

QUANTUM_FACTOR = "GROWTH"

QUANTUM_TOP_N = 2

QUANTUM_MIN_COMPONENTS = 2

QUANTUM_GROWTH_HIGHER_IS_BETTER = (
    "revenue_growth",
    "eps_growth",
    "operating_cash_flow_growth",
)


# =============================================================================
# METODOLOGIA DO RANKING FUNDAMENTAL
# =============================================================================

FUNDAMENTAL_WINSORIZATION_LOWER = 0.05
FUNDAMENTAL_WINSORIZATION_UPPER = 0.95

FUNDAMENTAL_USE_PERCENTILE_RANK = True

FUNDAMENTAL_SCORE_METHOD = "MEAN_VALID_COMPONENTS"

FUNDAMENTAL_RANK_ASCENDING = False


# =============================================================================
# TIMING — ROBOTICS
# =============================================================================

ROBOTICS_TIMING_ENABLED = True

ROBOTICS_TIMING_ENGINE = "AI_INFRASTRUCTURE_SIGNAL_ENGINE"

ROBOTICS_TIMING_FOR_ENTRY = True

ROBOTICS_TIMING_FOR_NEW_CONTRIBUTION = True

ROBOTICS_TIMING_FOR_OWNERSHIP = False

ROBOTICS_TIMING_FOR_SELL = False


# =============================================================================
# TIMING — QUANTUM
# =============================================================================

QUANTUM_TIMING_ENABLED = False

QUANTUM_TIMING_ENGINE = None

QUANTUM_TIMING_FOR_ENTRY = False

QUANTUM_TIMING_FOR_NEW_CONTRIBUTION = False

QUANTUM_TIMING_FOR_OWNERSHIP = False

QUANTUM_TIMING_FOR_SELL = False


# =============================================================================
# POLÍTICA DE PROPRIEDADE
# =============================================================================

OWNERSHIP_DEFINED_BY_FUNDAMENTALS = True

EXIT_WHEN_NO_LONGER_FUNDAMENTALLY_SELECTED = True

PRICE_DROP_IS_SELL_SIGNAL = False

TIMING_SIGNAL_IS_SELL_SIGNAL = False

TIMING_CAN_REMOVE_SELECTED_COMPANY = False

TIMING_CAN_CHANGE_FUNDAMENTAL_RANK = False


# =============================================================================
# SEGURANÇA METODOLÓGICA
# =============================================================================

ALLOW_LOOKAHEAD = False

ALLOW_FUTURE_RETURNS_IN_SIGNAL = False

STRICT_POINT_IN_TIME = True


# =============================================================================
# PREÇOS
# =============================================================================

USE_ADJUSTED_PRICES = True

PRICE_HISTORY_YEARS = 5

BENCHMARK_TICKER = "^GSPC"


# =============================================================================
# SEC
# =============================================================================

SEC_COMPANYFACTS_URL = (
    "https://data.sec.gov/api/xbrl/companyfacts/"
    "CIK{cik}.json"
)

SEC_TICKER_CIK_URL = (
    "https://www.sec.gov/files/company_tickers.json"
)

SEC_USER_AGENT = (
    "ROBOTICS_QUANTUM_SP500 "
    "research@example.com"
)


# =============================================================================
# S&P 500
# =============================================================================

SP500_SOURCE_URL = (
    "https://en.wikipedia.org/wiki/"
    "List_of_S%26P_500_companies"
)


# =============================================================================
# SAÍDAS
# =============================================================================

CURRENT_UNIVERSE_FILE = (
    OUTPUT_DIR / "sp500_current.csv"
)

THEMATIC_UNIVERSE_FILE = (
    OUTPUT_DIR / "thematic_universe.csv"
)

FUNDAMENTAL_SNAPSHOT_FILE = (
    OUTPUT_DIR / "fundamental_snapshot.csv"
)

FUNDAMENTAL_SELECTION_FILE = (
    OUTPUT_DIR / "fundamental_selection.csv"
)

ROBOTICS_TIMING_FILE = (
    OUTPUT_DIR / "robotics_timing.csv"
)

FINAL_SELECTION_FILE = (
    OUTPUT_DIR / "final_selection.csv"
)

FINAL_REPORT_FILE = (
    OUTPUT_DIR / "robotics_quantum_report.xlsx"
)


# =============================================================================
# CRIAÇÃO DOS DIRETÓRIOS
# =============================================================================

for directory in (
    DATA_DIR,
    REPORTS_DIR,
    OUTPUT_DIR,
    CACHE_DIR,
):
    directory.mkdir(
        parents=True,
        exist_ok=True,
    )


# =============================================================================
# VALIDAÇÕES DE SEGURANÇA
# =============================================================================

assert UNIVERSE_NAME == "S&P 500"

assert ROBOTICS_FACTOR == "FINANCIAL_STRENGTH"
assert ROBOTICS_TOP_N == 5

assert QUANTUM_FACTOR == "GROWTH"
assert QUANTUM_TOP_N == 2

assert ROBOTICS_TIMING_ENABLED is True
assert QUANTUM_TIMING_ENABLED is False

assert ROBOTICS_TIMING_FOR_OWNERSHIP is False
assert ROBOTICS_TIMING_FOR_SELL is False

assert QUANTUM_TIMING_FOR_OWNERSHIP is False
assert QUANTUM_TIMING_FOR_SELL is False

assert TIMING_SIGNAL_IS_SELL_SIGNAL is False
assert TIMING_CAN_REMOVE_SELECTED_COMPANY is False
assert TIMING_CAN_CHANGE_FUNDAMENTAL_RANK is False

assert ALLOW_LOOKAHEAD is False
assert ALLOW_FUTURE_RETURNS_IN_SIGNAL is False


# =============================================================================
# RESUMO DA POLÍTICA
# =============================================================================

FROZEN_POLICY = {
    "ROBOTICS": {
        "factor": ROBOTICS_FACTOR,
        "top_n": ROBOTICS_TOP_N,
        "timing": ROBOTICS_TIMING_ENGINE,
    },
    "QUANTUM": {
        "factor": QUANTUM_FACTOR,
        "top_n": QUANTUM_TOP_N,
        "timing": QUANTUM_TIMING_ENGINE,
    },
}
