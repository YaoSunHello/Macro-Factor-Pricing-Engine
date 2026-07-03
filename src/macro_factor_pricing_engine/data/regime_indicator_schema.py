"""Point-in-time raw indicator schema for regime classification."""

from __future__ import annotations

from dataclasses import dataclass, fields
from datetime import date


REGIME_INDICATOR_FIELDS: tuple[str, ...] = (
    "ism_manufacturing_pmi",
    "chicago_fed_nai",
    "gdpnow_estimate",
    "cpi_yoy",
    "core_cpi_yoy",
    "breakeven_5y5y",
    "ust_2y_yield",
    "ust_2y_yield_chg_1m",
    "ust_10y_yield",
    "ust_10y_yield_chg_1m",
    "fed_funds_implied_path_chg_3m",
    "nfci",
    "ig_oas",
    "ig_oas_chg_1m",
    "hy_oas",
    "hy_oas_chg_1m",
    "vix",
    "acm_term_premium_10y",
    "dxy_chg_3m",
    "dxy_trend_direction",
    "broad_commodity_index_chg_3m",
    "sp500_drawdown_from_52w_high",
)


@dataclass(frozen=True)
class RegimeIndicatorSnapshot:
    """Raw public-data inputs observed as of a snapshot date.

    Indicator values are intentionally nullable. A missing value must remain
    missing through classification and be exposed to callers; it is never silently
    imputed. Lag fields record how many days old the observation was on
    ``snapshot_date`` and support no-lookahead checks.
    """

    snapshot_date: date
    ism_manufacturing_pmi: float | None
    chicago_fed_nai: float | None
    gdpnow_estimate: float | None
    cpi_yoy: float | None
    core_cpi_yoy: float | None
    breakeven_5y5y: float | None
    ust_2y_yield: float | None
    ust_2y_yield_chg_1m: float | None
    ust_10y_yield: float | None
    ust_10y_yield_chg_1m: float | None
    fed_funds_implied_path_chg_3m: float | None
    nfci: float | None
    ig_oas: float | None
    ig_oas_chg_1m: float | None
    hy_oas: float | None
    hy_oas_chg_1m: float | None
    vix: float | None
    acm_term_premium_10y: float | None
    dxy_chg_3m: float | None
    dxy_trend_direction: float | None
    broad_commodity_index_chg_3m: float | None
    sp500_drawdown_from_52w_high: float | None
    ism_manufacturing_pmi_as_of_lag_days: int = 0
    chicago_fed_nai_as_of_lag_days: int = 0
    gdpnow_estimate_as_of_lag_days: int = 0
    cpi_yoy_as_of_lag_days: int = 0
    core_cpi_yoy_as_of_lag_days: int = 0
    breakeven_5y5y_as_of_lag_days: int = 0
    ust_2y_yield_as_of_lag_days: int = 0
    ust_2y_yield_chg_1m_as_of_lag_days: int = 0
    ust_10y_yield_as_of_lag_days: int = 0
    ust_10y_yield_chg_1m_as_of_lag_days: int = 0
    fed_funds_implied_path_chg_3m_as_of_lag_days: int = 0
    nfci_as_of_lag_days: int = 0
    ig_oas_as_of_lag_days: int = 0
    ig_oas_chg_1m_as_of_lag_days: int = 0
    hy_oas_as_of_lag_days: int = 0
    hy_oas_chg_1m_as_of_lag_days: int = 0
    vix_as_of_lag_days: int = 0
    acm_term_premium_10y_as_of_lag_days: int = 0
    dxy_chg_3m_as_of_lag_days: int = 0
    dxy_trend_direction_as_of_lag_days: int = 0
    broad_commodity_index_chg_3m_as_of_lag_days: int = 0
    sp500_drawdown_from_52w_high_as_of_lag_days: int = 0

    @property
    def missing_fields(self) -> frozenset[str]:
        """Return raw indicator names with missing values."""
        return frozenset(
            field.name
            for field in fields(self)
            if field.name in REGIME_INDICATOR_FIELDS and getattr(self, field.name) is None
        )

    def as_of_lag_days_for(self, field_name: str) -> int:
        """Return the recorded observation lag for a raw indicator field."""
        if field_name not in REGIME_INDICATOR_FIELDS:
            raise KeyError(f"Unknown regime indicator field: {field_name}")
        return getattr(self, f"{field_name}_as_of_lag_days")
