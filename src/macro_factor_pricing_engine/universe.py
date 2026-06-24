"""UK-retail-accessible asset class universe.

Membership and allocation approval are deliberately separate. The universe is
populated with representative UCITS/LSE-listed instruments for research scope,
but every security remains unapproved for allocation.
"""

from __future__ import annotations


def _sec(
    ticker: str,
    bucket: str,
    role: str,
    ccy: str,
    domicile: str,
    listing: str,
    isin: str | None,
    replaces: str | None,
    duration_proxy_years: float | None = None,
) -> dict[str, object]:
    """Build a security record with approval deliberately left closed."""
    security: dict[str, object] = {
        "ticker": ticker,
        "bucket": bucket,
        "role": role,
        "ccy": ccy,
        "domicile": domicile,
        "listing": listing,
        "isin": isin,
        "replaces": replaces,
        "approved_for_allocation": False,
    }
    if duration_proxy_years is not None:
        security["duration_proxy_years"] = duration_proxy_years
    return security


ASSET_CLASS_UNIVERSE: dict[str, dict[str, dict[str, object]]] = {
    "us_equities": {
        "CSPX": _sec(
            "CSPX",
            "us_equities",
            "S&P 500 accumulating UCITS ETF - USER TO CONFIRM",
            "USD",
            "Ireland",
            "LSE",
            "IE00B5BMR087",
            None,
        ),
        "VUSA": _sec(
            "VUSA",
            "us_equities",
            "S&P 500 distributing UCITS ETF - USER TO CONFIRM",
            "USD",
            "Ireland",
            "LSE",
            "IE00B3XXRP09",
            None,
        ),
    },
    "global_developed_equities": {
        "SWDA": _sec(
            "SWDA",
            "global_developed_equities",
            "MSCI World accumulating UCITS ETF - USER TO CONFIRM",
            "USD",
            "Ireland",
            "LSE",
            "IE00B4L5Y983",
            None,
        ),
        "VEVE": _sec(
            "VEVE",
            "global_developed_equities",
            "FTSE Developed World distributing UCITS ETF - USER TO CONFIRM",
            "USD",
            "Ireland",
            "LSE",
            "IE00BKX55T58",
            None,
        ),
    },
    "emerging_market_equities": {
        "EIMI": _sec(
            "EIMI",
            "emerging_market_equities",
            "MSCI Emerging Markets IMI accumulating UCITS ETF - USER TO CONFIRM",
            "USD",
            "Ireland",
            "LSE",
            "IE00BKM4GZ66",
            None,
        ),
        "VFEM": _sec(
            "VFEM",
            "emerging_market_equities",
            "FTSE Emerging Markets distributing UCITS ETF - USER TO CONFIRM",
            "USD",
            "Ireland",
            "LSE",
            "IE00B3VVMM84",
            None,
        ),
    },
    "short_duration_government_bonds": {
        "IB01": _sec(
            "IB01",
            "short_duration_government_bonds",
            "0-1 year US Treasury UCITS ETF - USER TO CONFIRM",
            "USD",
            "Ireland",
            "LSE",
            None,  # TODO confirm ISIN.
            "SHV",
            0.4,
        ),
        "IBTA": _sec(
            "IBTA",
            "short_duration_government_bonds",
            "1-3 year US Treasury UCITS ETF - USER TO CONFIRM",
            "USD",
            "Ireland",
            "LSE",
            None,  # TODO confirm ISIN.
            "SHY",
            1.9,
        ),
    },
    "intermediate_duration_government_bonds": {
        "IBTM": _sec(
            "IBTM",
            "intermediate_duration_government_bonds",
            "7-10 year US Treasury UCITS ETF - USER TO CONFIRM",
            "USD",
            "Ireland",
            "LSE",
            None,  # TODO confirm ISIN.
            "IEF",
            7.5,
        ),
        # TODO: no clean single-line UCITS twin confirmed for VGIT's 3-10y blend.
    },
    "long_duration_government_bonds": {
        "IDTL": _sec(
            "IDTL",
            "long_duration_government_bonds",
            "20+ year US Treasury accumulating UCITS ETF - USER TO CONFIRM",
            "USD",
            "Ireland",
            "LSE",
            None,  # TODO confirm ISIN.
            "TLT",
            16.5,
        ),
        "DTLA": _sec(
            "DTLA",
            "long_duration_government_bonds",
            "20+ year US Treasury distributing UCITS ETF - USER TO CONFIRM",
            "USD",
            "Ireland",
            "LSE",
            None,  # TODO confirm ISIN.
            "VGLT",
            16.5,
        ),
    },
    "inflation_linked_bonds": {
        "ITPS": _sec(
            "ITPS",
            "inflation_linked_bonds",
            "Broad US TIPS UCITS ETF - USER TO CONFIRM",
            "USD",
            "Ireland",
            "LSE",
            None,  # TODO confirm ISIN.
            "TIP",
            6.5,
        ),
        # TODO: short-TIPS / 5y-breakeven UCITS twin for VTIP is unverified.
    },
    "investment_grade_credit": {
        "LQDE": _sec(
            "LQDE",
            "investment_grade_credit",
            "USD investment-grade corporate bond UCITS ETF - USER TO CONFIRM",
            "USD",
            "Ireland",
            "LSE",
            None,  # TODO confirm ISIN.
            None,
        ),
    },
    "high_yield_credit": {
        "IHYU": _sec(
            "IHYU",
            "high_yield_credit",
            "USD high-yield corporate bond UCITS ETF - USER TO CONFIRM",
            "USD",
            "Ireland",
            "LSE",
            None,  # TODO confirm ISIN.
            None,
        ),
    },
    "gold": {
        "SGLN": _sec(
            "SGLN",
            "gold",
            "iShares Physical Gold ETC - USER TO CONFIRM",
            "USD",
            "Ireland",
            "LSE",
            "IE00B4ND3602",
            None,
        ),
        "SGLD": _sec(
            "SGLD",
            "gold",
            "Invesco Physical Gold ETC - USER TO CONFIRM",
            "USD",
            "Ireland",
            "LSE",
            None,  # TODO confirm ISIN.
            None,
        ),
    },
    "broad_commodities": {
        "CMOD": _sec(
            "CMOD",
            "broad_commodities",
            "Invesco Bloomberg Commodity UCITS ETF - USER TO CONFIRM",
            "USD",
            "Ireland",
            "LSE",
            None,  # TODO confirm ISIN.
            None,
        ),
        "ICOM": _sec(
            "ICOM",
            "broad_commodities",
            "iShares diversified commodity swap UCITS ETF - USER TO CONFIRM",
            "USD",
            "Ireland",
            "LSE",
            None,  # TODO confirm ISIN.
            None,
        ),
    },
    "usd_proxy": {
        "IB01": _sec(
            "IB01",
            "usd_proxy",
            "USD cash-rate proxy via 0-1 year US Treasury UCITS ETF - USER TO CONFIRM",
            "USD",
            "Ireland",
            "LSE",
            None,  # TODO confirm ISIN.
            None,
            0.4,
        ),
    },
    "cash": {
        "IGLS": _sec(
            "IGLS",
            "cash",
            "GBP near-cash proxy via 0-5 year gilt UCITS ETF - USER TO CONFIRM",
            "GBP",
            "Ireland",
            "LSE",
            None,  # TODO confirm ISIN.
            None,
            2.3,
        ),
    },
}

ASSET_CLASS_SCORING_MODULES: dict[str, str | None] = {
    asset_class: None for asset_class in ASSET_CLASS_UNIVERSE
}

PLATFORM_ACCESS: dict[str, dict[str, bool]] = {
    "ibkr_uk": {
        "ucits_etfs": True,
        "us_listed_stocks": True,
        "us_domiciled_etfs": False,
        "futures": True,
        "fx_spot": True,
        "options": True,
        "cfds": False,
    },
    "trading212": {
        "ucits_etfs": True,
        "us_listed_stocks": False,
        "us_domiciled_etfs": False,
        "futures": False,
        "fx_spot": False,
        "options": False,
        "cfds": True,
    },
    "hargreaves_lansdown": {
        "ucits_etfs": True,
        "us_listed_stocks": False,
        "us_domiciled_etfs": False,
        "futures": False,
        "fx_spot": False,
        "options": False,
        "cfds": False,
    },
    "aj_bell": {
        "ucits_etfs": True,
        "us_listed_stocks": False,
        "us_domiciled_etfs": False,
        "futures": False,
        "fx_spot": False,
        "options": False,
        "cfds": False,
    },
    "investengine": {
        "ucits_etfs": True,
        "us_listed_stocks": False,
        "us_domiciled_etfs": False,
        "futures": False,
        "fx_spot": False,
        "options": False,
        "cfds": False,
    },
}


def asset_classes() -> tuple[str, ...]:
    """Return the approved asset classes with current research-scope membership."""
    return tuple(ASSET_CLASS_UNIVERSE)


def scoring_module_for(asset_class: str) -> str | None:
    """Return the optional scoring module reference for an asset class."""
    return ASSET_CLASS_SCORING_MODULES[asset_class]


def has_tradeable_instruments() -> bool:
    """Return whether any asset class has approved instruments."""
    return any(
        bool(security.get("approved_for_allocation"))
        for instruments in ASSET_CLASS_UNIVERSE.values()
        for security in instruments.values()
    )


def rates_securities() -> tuple[dict[str, object], ...]:
    """Return in-scope rates securities, regardless of approval status."""
    buckets = (
        "short_duration_government_bonds",
        "intermediate_duration_government_bonds",
        "long_duration_government_bonds",
        "inflation_linked_bonds",
    )
    return tuple(
        security
        for bucket in buckets
        for security in ASSET_CLASS_UNIVERSE[bucket].values()
    )


def platforms() -> tuple[str, ...]:
    """Return the platform identifiers covered by the capability matrix."""
    return tuple(PLATFORM_ACCESS)


def platform_supports(platform: str, capability: str) -> bool:
    """Return whether a platform supports a capability."""
    return PLATFORM_ACCESS[platform][capability]
