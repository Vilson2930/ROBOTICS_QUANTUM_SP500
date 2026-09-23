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

IMPORTANTE:
Os parâmetros técnicos do AI Infrastructure Scanner são
preservados para manter compatibilidade com os motores
originais de timing.
"""

from pathlib import Path


# =============================================================================
# PROJETO
# =============================================================================

PROJECT_NAME = "ROBOTICS_QUANTUM_SP500"

VERSION = "1.0.0"

# Compatibilidade com módulos que utilizem o nome anterior.
PROJECT_VERSION = VERSION

AUTHOR = "Vilson Pinto"

DESCRIPTION = (
    "Scanner do S&P 500 para seleção fundamental de empresas "
    "ligadas a Robotics e Quantum Computing, com timing técnico "
    "aplicado exclusivamente às empresas Robotics selecionadas."
)


# =============================================================================
# PASTAS
# =============================================================================

BASE_DIR = Path(__file__).resolve().parent.parent

# Compatibilidade com o AI Infrastructure Scanner.
ROOT = BASE_DIR

DATA_DIR = BASE_DIR / "data"
REPORTS_DIR = BASE_DIR / "reports"
OUTPUT_DIR = BASE_DIR / "output"
CACHE_DIR = BASE_DIR / "cache"

# Nomes utilizados pelos módulos originais.
DATA_PATH = DATA_DIR
REPORT_PATH = REPORTS_DIR


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

ROBOTICS_TIMING_ENGINE = (
    "AI_INFRASTRUCTURE_SIGNAL_ENGINE"
)

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
# PREÇOS — NOVO ROBÔ
# =============================================================================

USE_ADJUSTED_PRICES = True

PRICE_HISTORY_YEARS = 5

BENCHMARK_TICKER = "^GSPC"


# =============================================================================
# MARKET DATA — COMPATIBILIDADE COM AI INFRASTRUCTURE SCANNER
# =============================================================================

# Valores originais preservados.

PERIOD = "3y"

INTERVAL = "1d"

MIN_DOLLAR_VOLUME = 100_000_000

MIN_HISTORY = 250


# =============================================================================
# INDICADORES TÉCNICOS
# =============================================================================
#
# PARÂMETROS ORIGINAIS DO AI INFRASTRUCTURE SCANNER.
# NÃO OTIMIZAR AUTOMATICAMENTE.
# =============================================================================

RSI_PERIOD = 14

ADX_PERIOD = 14

ATR_PERIOD = 14

MFI_PERIOD = 14

MACD_FAST = 12

MACD_SLOW = 26

MACD_SIGNAL = 9

SMA_SHORT = 20

SMA_MEDIUM = 50

SMA_LONG = 200

VOLUME_WINDOW = 20


# =============================================================================
# SCORING — AI INFRASTRUCTURE SCANNER
# =============================================================================

MAX_SCORE = 100


# =============================================================================
# TECHNICAL ENTRY SCORE
# =============================================================================
#
# Pesos originais preservados.
# =============================================================================

WEIGHT_DISCOUNT = 25

WEIGHT_MOMENTUM = 20

WEIGHT_TREND = 20

WEIGHT_VOLUME = 20

WEIGHT_RISK = 15


# =============================================================================
# INSTITUTIONAL SCORE
# =============================================================================
#
# Pesos originais preservados.
# =============================================================================

WEIGHT_GROWTH = 30

WEIGHT_MARKET_LEADER = 20

WEIGHT_LIQUIDITY = 20

WEIGHT_HYPE = 15

WEIGHT_SECTOR = 15


# =============================================================================
# RANKING / SIGNAL — COMPATIBILIDADE
# =============================================================================

WEIGHT_INSTITUTIONAL = 50

WEIGHT_TECHNICAL = 50


# =============================================================================
# CRITÉRIOS ORIGINAIS DO SCANNER
# =============================================================================

MIN_TECHNICAL_SCORE = 70

MIN_INSTITUTIONAL_SCORE = 65

MIN_FINAL_SCORE = 70


# =============================================================================
# RELATÓRIO / DISPLAY
# =============================================================================

TOP_N = 20


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
# ARQUIVOS — NOVO ROBÔ
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
# ARQUIVOS — MOTORES ORIGINAIS DE TIMING
# =============================================================================
#
# Estes nomes são necessários porque os módulos copiados do
# AI Infrastructure Scanner importam diretamente estas constantes.
# =============================================================================

PRICE_FILE = (
    DATA_PATH / "historico_precos.csv"
)

INDICATOR_FILE = (
    DATA_PATH / "indicadores.csv"
)

INSTITUTIONAL_SCORE_FILE = (
    DATA_PATH / "institutional_score.csv"
)

TECHNICAL_SCORE_FILE = (
    DATA_PATH / "technical_score.csv"
)

ENTRY_TIMING_SCORE_FILE = (
    DATA_PATH / "entry_timing_score.csv"
)

SIGNAL_FILE = (
    DATA_PATH / "signals.csv"
)

RANKING_FILE = (
    DATA_PATH / "ranking.csv"
)

REPORT_FILE = (
    REPORTS_DIR / "relatorio.xlsx"
)


# =============================================================================
# CORES — COMPATIBILIDADE
# =============================================================================

COLOR_BUY = "#16A34A"

COLOR_WAIT = "#EAB308"

COLOR_SELL = "#DC2626"


# =============================================================================
# LOG
# =============================================================================

SHOW_PROGRESS = True

VERBOSE = True


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
# VALIDAÇÕES DA ARQUITETURA
# =============================================================================

assert UNIVERSE_NAME == "S&P 500"

assert REQUIRE_SP500_MEMBERSHIP is True


# ROBOTICS

assert ROBOTICS_FACTOR == "FINANCIAL_STRENGTH"

assert ROBOTICS_TOP_N == 5

assert ROBOTICS_MIN_COMPONENTS == 2


# QUANTUM

assert QUANTUM_FACTOR == "GROWTH"

assert QUANTUM_TOP_N == 2

assert QUANTUM_MIN_COMPONENTS == 2


# TIMING

assert ROBOTICS_TIMING_ENABLED is True

assert QUANTUM_TIMING_ENABLED is False

assert ROBOTICS_TIMING_FOR_OWNERSHIP is False

assert ROBOTICS_TIMING_FOR_SELL is False

assert QUANTUM_TIMING_FOR_OWNERSHIP is False

assert QUANTUM_TIMING_FOR_SELL is False


# OWNERSHIP

assert OWNERSHIP_DEFINED_BY_FUNDAMENTALS is True

assert TIMING_SIGNAL_IS_SELL_SIGNAL is False

assert TIMING_CAN_REMOVE_SELECTED_COMPANY is False

assert TIMING_CAN_CHANGE_FUNDAMENTAL_RANK is False


# LOOK-AHEAD

assert ALLOW_LOOKAHEAD is False

assert ALLOW_FUTURE_RETURNS_IN_SIGNAL is False

assert STRICT_POINT_IN_TIME is True


# =============================================================================
# VALIDAÇÃO DOS PARÂMETROS ORIGINAIS DO TIMING
# =============================================================================

assert RSI_PERIOD == 14

assert ADX_PERIOD == 14

assert ATR_PERIOD == 14

assert MFI_PERIOD == 14

assert MACD_FAST == 12

assert MACD_SLOW == 26

assert MACD_SIGNAL == 9

assert SMA_SHORT == 20

assert SMA_MEDIUM == 50

assert SMA_LONG == 200

assert VOLUME_WINDOW == 20

assert MIN_TECHNICAL_SCORE == 70

assert MIN_INSTITUTIONAL_SCORE == 65

assert MIN_FINAL_SCORE == 70


# =============================================================================
# POLÍTICA CONGELADA
# =============================================================================

FROZEN_POLICY = {
    "ROBOTICS": {
        "factor": ROBOTICS_FACTOR,
        "top_n": ROBOTICS_TOP_N,
        "timing": ROBOTICS_TIMING_ENGINE,
        "timing_for_entry": True,
        "timing_for_ownership": False,
        "timing_for_sell": False,
    },
    "QUANTUM": {
        "factor": QUANTUM_FACTOR,
        "top_n": QUANTUM_TOP_N,
        "timing": QUANTUM_TIMING_ENGINE,
        "timing_for_entry": False,
        "timing_for_ownership": False,
        "timing_for_sell": False,
    },
}
