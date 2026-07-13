from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import date, datetime, time
from typing import Any, Iterable
from zoneinfo import ZoneInfo

import pandas as pd


NEW_YORK = ZoneInfo("America/New_York")


@dataclass(frozen=True)
class IntradayMarketSpec:
    market_id: str
    symbol: str
    display_name: str
    asset_class: str
    exchange: str
    data_timezone: str
    orb_anchor_timezone: str
    orb_session_start: str
    orb_session_end: str
    default_bar_minutes: int
    minimum_tick: float
    contract_multiplier: float
    tick_value: float
    requires_contract_roll: bool
    historical_data_adapter: str
    transfer_family: str

    def validate(self) -> None:
        if not self.market_id.strip():
            raise ValueError("market_id cannot be empty.")

        if self.asset_class not in {
            "etf",
            "futures",
        }:
            raise ValueError(
                f"Unsupported asset class: {self.asset_class}"
            )

        if self.default_bar_minutes <= 0:
            raise ValueError(
                "default_bar_minutes must be positive."
            )

        if self.minimum_tick <= 0:
            raise ValueError(
                "minimum_tick must be positive."
            )

        if self.contract_multiplier <= 0:
            raise ValueError(
                "contract_multiplier must be positive."
            )

        expected_tick_value = (
            self.minimum_tick
            * self.contract_multiplier
        )

        if abs(
            expected_tick_value
            - self.tick_value
        ) > 1e-12:
            raise ValueError(
                f"{self.market_id} tick value does not equal "
                "minimum_tick × contract_multiplier."
            )

        ZoneInfo(self.data_timezone)
        ZoneInfo(self.orb_anchor_timezone)

        _parse_clock(self.orb_session_start)
        _parse_clock(self.orb_session_end)

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        return asdict(self)


INTRADAY_MARKETS: dict[
    str,
    IntradayMarketSpec,
] = {
    "QQQ": IntradayMarketSpec(
        market_id="QQQ",
        symbol="QQQ",
        display_name="Invesco QQQ ETF",
        asset_class="etf",
        exchange="NASDAQ",
        data_timezone="America/New_York",
        orb_anchor_timezone="America/New_York",
        orb_session_start="09:30",
        orb_session_end="16:00",
        default_bar_minutes=5,
        minimum_tick=0.01,
        contract_multiplier=1.0,
        tick_value=0.01,
        requires_contract_roll=False,
        historical_data_adapter="alpaca_sip_equities",
        transfer_family="nasdaq_100",
    ),
    "SPY": IntradayMarketSpec(
        market_id="SPY",
        symbol="SPY",
        display_name="SPDR S&P 500 ETF Trust",
        asset_class="etf",
        exchange="NYSE_ARCA",
        data_timezone="America/New_York",
        orb_anchor_timezone="America/New_York",
        orb_session_start="09:30",
        orb_session_end="16:00",
        default_bar_minutes=5,
        minimum_tick=0.01,
        contract_multiplier=1.0,
        tick_value=0.01,
        requires_contract_roll=False,
        historical_data_adapter="alpaca_sip_equities",
        transfer_family="sp_500",
    ),
    "NQ": IntradayMarketSpec(
        market_id="NQ",
        symbol="NQ",
        display_name="E-mini Nasdaq-100 Futures",
        asset_class="futures",
        exchange="CME",
        data_timezone="America/Chicago",
        orb_anchor_timezone="America/New_York",
        orb_session_start="09:30",
        orb_session_end="16:00",
        default_bar_minutes=5,
        minimum_tick=0.25,
        contract_multiplier=20.0,
        tick_value=5.0,
        requires_contract_roll=True,
        historical_data_adapter="futures_provider_required",
        transfer_family="nasdaq_100",
    ),
    "MNQ": IntradayMarketSpec(
        market_id="MNQ",
        symbol="MNQ",
        display_name="Micro E-mini Nasdaq-100 Futures",
        asset_class="futures",
        exchange="CME",
        data_timezone="America/Chicago",
        orb_anchor_timezone="America/New_York",
        orb_session_start="09:30",
        orb_session_end="16:00",
        default_bar_minutes=5,
        minimum_tick=0.25,
        contract_multiplier=2.0,
        tick_value=0.50,
        requires_contract_roll=True,
        historical_data_adapter="futures_provider_required",
        transfer_family="nasdaq_100",
    ),
    "ES": IntradayMarketSpec(
        market_id="ES",
        symbol="ES",
        display_name="E-mini S&P 500 Futures",
        asset_class="futures",
        exchange="CME",
        data_timezone="America/Chicago",
        orb_anchor_timezone="America/New_York",
        orb_session_start="09:30",
        orb_session_end="16:00",
        default_bar_minutes=5,
        minimum_tick=0.25,
        contract_multiplier=50.0,
        tick_value=12.50,
        requires_contract_roll=True,
        historical_data_adapter="futures_provider_required",
        transfer_family="sp_500",
    ),
    "MES": IntradayMarketSpec(
        market_id="MES",
        symbol="MES",
        display_name="Micro E-mini S&P 500 Futures",
        asset_class="futures",
        exchange="CME",
        data_timezone="America/Chicago",
        orb_anchor_timezone="America/New_York",
        orb_session_start="09:30",
        orb_session_end="16:00",
        default_bar_minutes=5,
        minimum_tick=0.25,
        contract_multiplier=5.0,
        tick_value=1.25,
        requires_contract_roll=True,
        historical_data_adapter="futures_provider_required",
        transfer_family="sp_500",
    ),
}


def _parse_clock(value: str) -> time:
    return datetime.strptime(
        value,
        "%H:%M",
    ).time()


def validate_intraday_market_registry() -> None:
    if len(INTRADAY_MARKETS) != len(
        set(INTRADAY_MARKETS)
    ):
        raise ValueError(
            "Duplicate intraday market IDs detected."
        )

    symbols: list[str] = []

    for market_id, specification in (
        INTRADAY_MARKETS.items()
    ):
        if market_id != specification.market_id:
            raise ValueError(
                "Registry key and market_id do not match."
            )

        specification.validate()
        symbols.append(specification.symbol)

    if len(symbols) != len(set(symbols)):
        raise ValueError(
            "Duplicate market symbols detected."
        )


def get_intraday_market(
    market_id: str,
) -> IntradayMarketSpec:
    normalized = market_id.strip().upper()

    if normalized not in INTRADAY_MARKETS:
        raise KeyError(
            f"Unknown intraday market: {market_id}"
        )

    specification = INTRADAY_MARKETS[
        normalized
    ]

    specification.validate()
    return specification


def list_intraday_markets(
) -> list[IntradayMarketSpec]:
    validate_intraday_market_registry()

    return [
        INTRADAY_MARKETS[key]
        for key in sorted(
            INTRADAY_MARKETS
        )
    ]


def expected_regular_session_index(
    session_date: date | str | pd.Timestamp,
    *,
    bar_minutes: int = 5,
    timezone_name: str = "America/New_York",
    session_start: str = "09:30",
    session_end: str = "16:00",
) -> pd.DatetimeIndex:
    if bar_minutes <= 0:
        raise ValueError(
            "bar_minutes must be positive."
        )

    timezone = ZoneInfo(timezone_name)
    day = pd.Timestamp(session_date).date()

    start_clock = _parse_clock(session_start)
    end_clock = _parse_clock(session_end)

    start = pd.Timestamp(
        datetime.combine(
            day,
            start_clock,
            tzinfo=timezone,
        )
    )

    end = pd.Timestamp(
        datetime.combine(
            day,
            end_clock,
            tzinfo=timezone,
        )
    )

    if end <= start:
        raise ValueError(
            "session_end must follow session_start."
        )

    return pd.date_range(
        start=start,
        end=end,
        freq=f"{bar_minutes}min",
        inclusive="left",
        name="timestamp",
    )


def validate_complete_regular_session(
    data: pd.DataFrame,
    *,
    session_date: date | str | pd.Timestamp,
    market_id: str = "QQQ",
    required_columns: Iterable[str] = (
        "open",
        "high",
        "low",
        "close",
        "volume",
    ),
) -> None:
    market = get_intraday_market(
        market_id
    )

    if not isinstance(
        data.index,
        pd.DatetimeIndex,
    ):
        raise ValueError(
            "Intraday data must use a DatetimeIndex."
        )

    if data.index.tz is None:
        raise ValueError(
            "Intraday timestamps must be timezone-aware."
        )

    if data.index.has_duplicates:
        raise ValueError(
            "Duplicate intraday timestamps detected."
        )

    missing_columns = set(
        required_columns
    ).difference(data.columns)

    if missing_columns:
        raise ValueError(
            "Missing intraday columns: "
            f"{sorted(missing_columns)}"
        )

    local = data.copy()
    local.index = local.index.tz_convert(
        market.orb_anchor_timezone
    )

    expected = expected_regular_session_index(
        session_date,
        bar_minutes=(
            market.default_bar_minutes
        ),
        timezone_name=(
            market.orb_anchor_timezone
        ),
        session_start=(
            market.orb_session_start
        ),
        session_end=(
            market.orb_session_end
        ),
    )

    if not local.index.equals(expected):
        missing = expected.difference(
            local.index
        )

        unexpected = local.index.difference(
            expected
        )

        raise ValueError(
            "Session is incomplete or contains bars outside "
            f"the locked regular session. Missing={len(missing)}, "
            f"unexpected={len(unexpected)}."
        )

    prices = local[
        ["open", "high", "low", "close"]
    ].astype(float)

    if prices.isna().any().any():
        raise ValueError(
            "Intraday OHLC contains missing values."
        )

    if (prices <= 0).any().any():
        raise ValueError(
            "Intraday prices must be positive."
        )

    if (
        prices["high"]
        < prices[
            ["open", "low", "close"]
        ].max(axis=1)
    ).any():
        raise ValueError(
            "Invalid intraday high values detected."
        )

    if (
        prices["low"]
        > prices[
            ["open", "high", "close"]
        ].min(axis=1)
    ).any():
        raise ValueError(
            "Invalid intraday low values detected."
        )


if __name__ == "__main__":
    validate_intraday_market_registry()

    print(
        "Intraday market registry is valid."
    )
