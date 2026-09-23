"""
ROBOTICS_QUANTUM_SP500
======================

Universo temático oficial do robô.

IMPORTANTE
----------
A lista temática NÃO substitui o filtro do S&P 500.

Para uma empresa ser elegível ela precisa:

1. Estar atualmente no S&P 500.
2. Estar classificada neste universo como:
   - ROBOTICS
   - QUANTUM
   - BOTH

A classificação temática foi definida e auditada durante
o estudo realizado antes da implementação em produção.

Empresas BOTH participam independentemente dos rankings
Robotics e Quantum.
"""


# =============================================================================
# CLASSIFICAÇÕES PERMITIDAS
# =============================================================================

ALLOWED_THEMES = {
    "ROBOTICS",
    "QUANTUM",
    "BOTH",
}

ALLOWED_EXPOSURE_LEVELS = {
    "DIRECT",
    "STRATEGIC",
    "ENABLER",
}


# =============================================================================
# UNIVERSO TEMÁTICO CONGELADO
# =============================================================================

THEMATIC_UNIVERSE = {

    # =========================================================================
    # ROBOTICS — DIRECT
    # =========================================================================

    "ISRG": {
        "company": "Intuitive Surgical",
        "theme": "ROBOTICS",
        "exposure": "DIRECT",
    },

    "MDT": {
        "company": "Medtronic",
        "theme": "ROBOTICS",
        "exposure": "DIRECT",
    },

    "ROK": {
        "company": "Rockwell Automation",
        "theme": "ROBOTICS",
        "exposure": "DIRECT",
    },

    "SYK": {
        "company": "Stryker",
        "theme": "ROBOTICS",
        "exposure": "DIRECT",
    },

    "TER": {
        "company": "Teradyne",
        "theme": "ROBOTICS",
        "exposure": "DIRECT",
    },

    "ZBRA": {
        "company": "Zebra Technologies",
        "theme": "ROBOTICS",
        "exposure": "DIRECT",
    },


    # =========================================================================
    # ROBOTICS — STRATEGIC
    # =========================================================================

    "CAT": {
        "company": "Caterpillar",
        "theme": "ROBOTICS",
        "exposure": "STRATEGIC",
    },

    "DE": {
        "company": "Deere & Company",
        "theme": "ROBOTICS",
        "exposure": "STRATEGIC",
    },

    "TSLA": {
        "company": "Tesla",
        "theme": "ROBOTICS",
        "exposure": "STRATEGIC",
    },


    # =========================================================================
    # ROBOTICS — ENABLER
    # =========================================================================

    "ADI": {
        "company": "Analog Devices",
        "theme": "ROBOTICS",
        "exposure": "ENABLER",
    },

    "EMR": {
        "company": "Emerson Electric",
        "theme": "ROBOTICS",
        "exposure": "ENABLER",
    },

    "QCOM": {
        "company": "Qualcomm",
        "theme": "ROBOTICS",
        "exposure": "ENABLER",
    },

    "TXN": {
        "company": "Texas Instruments",
        "theme": "ROBOTICS",
        "exposure": "ENABLER",
    },


    # =========================================================================
    # QUANTUM — DIRECT
    # =========================================================================

    "GOOGL": {
        "company": "Alphabet",
        "theme": "QUANTUM",
        "exposure": "DIRECT",
    },

    "IBM": {
        "company": "IBM",
        "theme": "QUANTUM",
        "exposure": "DIRECT",
    },

    "INTC": {
        "company": "Intel",
        "theme": "QUANTUM",
        "exposure": "DIRECT",
    },

    "MSFT": {
        "company": "Microsoft",
        "theme": "QUANTUM",
        "exposure": "DIRECT",
    },


    # =========================================================================
    # QUANTUM — ENABLER
    # =========================================================================

    "KEYS": {
        "company": "Keysight Technologies",
        "theme": "QUANTUM",
        "exposure": "ENABLER",
    },


    # =========================================================================
    # BOTH — ROBOTICS + QUANTUM
    # =========================================================================

    "AMZN": {
        "company": "Amazon",
        "theme": "BOTH",
        "exposure": "STRATEGIC",
    },

    "HON": {
        "company": "Honeywell",
        "theme": "BOTH",
        "exposure": "STRATEGIC",
    },

    "NVDA": {
        "company": "NVIDIA",
        "theme": "BOTH",
        "exposure": "ENABLER",
    },
}


# =============================================================================
# FUNÇÕES
# =============================================================================

def normalize_ticker(ticker):
    """
    Normaliza ticker recebido pelo sistema.
    """

    if ticker is None:
        return None

    return (
        str(ticker)
        .strip()
        .upper()
        .replace(".", "-")
    )


def is_thematic_company(ticker):
    """
    Verifica se o ticker pertence ao universo temático.
    """

    ticker = normalize_ticker(ticker)

    return ticker in THEMATIC_UNIVERSE


def get_company_config(ticker):
    """
    Retorna a configuração temática da empresa.
    """

    ticker = normalize_ticker(ticker)

    return THEMATIC_UNIVERSE.get(ticker)


def get_theme(ticker):
    """
    Retorna ROBOTICS, QUANTUM ou BOTH.
    """

    config = get_company_config(ticker)

    if config is None:
        return None

    return config["theme"]


def get_exposure(ticker):
    """
    Retorna DIRECT, STRATEGIC ou ENABLER.
    """

    config = get_company_config(ticker)

    if config is None:
        return None

    return config["exposure"]


def participates_in_robotics(ticker):
    """
    Verifica participação no motor Robotics.
    """

    theme = get_theme(ticker)

    return theme in {
        "ROBOTICS",
        "BOTH",
    }


def participates_in_quantum(ticker):
    """
    Verifica participação no motor Quantum.
    """

    theme = get_theme(ticker)

    return theme in {
        "QUANTUM",
        "BOTH",
    }


def get_robotics_tickers():
    """
    Retorna todos os tickers do universo Robotics,
    incluindo empresas BOTH.
    """

    return sorted([
        ticker
        for ticker in THEMATIC_UNIVERSE
        if participates_in_robotics(ticker)
    ])


def get_quantum_tickers():
    """
    Retorna todos os tickers do universo Quantum,
    incluindo empresas BOTH.
    """

    return sorted([
        ticker
        for ticker in THEMATIC_UNIVERSE
        if participates_in_quantum(ticker)
    ])


def get_all_tickers():
    """
    Retorna todos os tickers temáticos.
    """

    return sorted(
        THEMATIC_UNIVERSE.keys()
    )


# =============================================================================
# VALIDAÇÃO
# =============================================================================

def validate_thematic_universe():
    """
    Valida integridade da configuração temática.
    """

    if len(THEMATIC_UNIVERSE) != 21:
        raise AssertionError(
            "O universo temático congelado deve possuir "
            "exatamente 21 empresas."
        )

    for ticker, config in THEMATIC_UNIVERSE.items():

        if not ticker:
            raise AssertionError(
                "Ticker vazio encontrado."
            )

        if config["theme"] not in ALLOWED_THEMES:
            raise AssertionError(
                f"Tema inválido para {ticker}: "
                f"{config['theme']}"
            )

        if config["exposure"] not in ALLOWED_EXPOSURE_LEVELS:
            raise AssertionError(
                f"Exposição inválida para {ticker}: "
                f"{config['exposure']}"
            )

        if not config.get("company"):
            raise AssertionError(
                f"Empresa sem nome: {ticker}"
            )


    robotics = get_robotics_tickers()
    quantum = get_quantum_tickers()

    # 13 Robotics exclusivos + 3 BOTH = 16
    assert len(robotics) == 16

    # 5 Quantum exclusivos + 3 BOTH = 8
    assert len(quantum) == 8

    assert participates_in_robotics("NVDA") is True
    assert participates_in_quantum("NVDA") is True

    assert participates_in_robotics("AMZN") is True
    assert participates_in_quantum("AMZN") is True

    assert participates_in_robotics("HON") is True
    assert participates_in_quantum("HON") is True

    return True


validate_thematic_universe()


# =============================================================================
# RESUMO
# =============================================================================

THEMATIC_SUMMARY = {
    "total_unique_companies":
        len(THEMATIC_UNIVERSE),

    "robotics_companies":
        len(get_robotics_tickers()),

    "quantum_companies":
        len(get_quantum_tickers()),

    "both_companies":
        sum(
            1
            for config in THEMATIC_UNIVERSE.values()
            if config["theme"] == "BOTH"
        ),
}
