"""Retail-accessible asset class universe.

Membership and allocation approval are deliberately separate. Rates sleeves have
starter proxies so the analysis loop can produce a pending paper recommendation,
but every security remains unapproved for allocation.
"""

ASSET_CLASS_UNIVERSE: dict[str, dict[str, dict[str, object]]] = {
    "us_equities": {},
    "global_developed_equities": {},
    "emerging_market_equities": {},
    "short_duration_government_bonds": {
        "SHY": {
            "ticker": "SHY",
            "bucket": "short_duration_government_bonds",
            "role": "1-3 year Treasury proxy - USER TO CONFIRM",
            "duration_proxy_years": 1.9,
            "approved_for_allocation": False,
        },
        "SHV": {
            "ticker": "SHV",
            "bucket": "short_duration_government_bonds",
            "role": "Treasury bills / ultra-short Treasury proxy - USER TO CONFIRM",
            "duration_proxy_years": 0.3,
            "approved_for_allocation": False,
        },
    },
    "intermediate_duration_government_bonds": {
        "IEF": {
            "ticker": "IEF",
            "bucket": "intermediate_duration_government_bonds",
            "role": "7-10 year Treasury proxy - USER TO CONFIRM",
            "duration_proxy_years": 7.4,
            "approved_for_allocation": False,
        },
        "VGIT": {
            "ticker": "VGIT",
            "bucket": "intermediate_duration_government_bonds",
            "role": "3-10 year Treasury proxy - USER TO CONFIRM",
            "duration_proxy_years": 5.2,
            "approved_for_allocation": False,
        },
    },
    "long_duration_government_bonds": {
        "TLT": {
            "ticker": "TLT",
            "bucket": "long_duration_government_bonds",
            "role": "20+ year Treasury proxy - USER TO CONFIRM",
            "duration_proxy_years": 16.5,
            "approved_for_allocation": False,
        },
        "VGLT": {
            "ticker": "VGLT",
            "bucket": "long_duration_government_bonds",
            "role": "long Treasury proxy - USER TO CONFIRM",
            "duration_proxy_years": 15.0,
            "approved_for_allocation": False,
        },
    },
    "inflation_linked_bonds": {
        "TIP": {
            "ticker": "TIP",
            "bucket": "inflation_linked_bonds",
            "role": "broad TIPS proxy - USER TO CONFIRM",
            "duration_proxy_years": 6.5,
            "approved_for_allocation": False,
        },
        "VTIP": {
            "ticker": "VTIP",
            "bucket": "inflation_linked_bonds",
            "role": "short TIPS / 5y breakeven proxy - USER TO CONFIRM",
            "duration_proxy_years": 2.5,
            "approved_for_allocation": False,
        },
    },
    "investment_grade_credit": {},
    "high_yield_credit": {},
    "gold": {},
    "broad_commodities": {},
    "usd_proxy": {},
    "cash": {},
}

ASSET_CLASS_SCORING_MODULES: dict[str, str | None] = {
    asset_class: None for asset_class in ASSET_CLASS_UNIVERSE
}


def asset_classes() -> tuple[str, ...]:
    """Return the approved asset classes with empty ticker selections."""
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
