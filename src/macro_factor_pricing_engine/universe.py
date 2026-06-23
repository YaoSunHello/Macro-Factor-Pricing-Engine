"""Retail-accessible asset class universe.

Ticker selection is intentionally left blank for now. The strategy can reason
about asset classes, but no instrument can be traded until tickers are approved.
"""

ASSET_CLASS_UNIVERSE: dict[str, dict[str, str]] = {
    "us_equities": {},
    "global_developed_equities": {},
    "emerging_market_equities": {},
    "short_duration_government_bonds": {},
    "intermediate_duration_government_bonds": {},
    "long_duration_government_bonds": {},
    "inflation_linked_bonds": {},
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
    return any(bool(instruments) for instruments in ASSET_CLASS_UNIVERSE.values())
