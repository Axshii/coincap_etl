import pytest

@pytest.fixture
def sample_assets_raw():
    """Fake API response — mirrors real CoinCap /assets output."""
    return [
        {
            "id": "bitcoin", "rank": "1", "symbol": "BTC",
            "name": "Bitcoin", "priceUsd": "65000.12",
            "marketCapUsd": "1200000000", "volumeUsd24Hr": "30000000",
            "changePercent24Hr": "2.5", "supply": "19000000",
            "maxSupply": "21000000", "vwap24Hr": "64500.00",
            "explorer": "", "tokens": {}
        },
        {
            "id": "ethereum", "rank": "2", "symbol": "ETH",
            "name": "Ethereum", "priceUsd": "3500.00",
            "marketCapUsd": "420000000", "volumeUsd24Hr": "15000000",
            "changePercent24Hr": "-1.2", "supply": "120000000",
            "maxSupply": None, "vwap24Hr": "3480.00",
            "explorer": "", "tokens": {}
        },
    ]


@pytest.fixture
def sample_history_raw():
    """Fake API response for /assets/{slug}/history."""
    return [
        {"slug": "bitcoin", "priceUsd": "64000.00",
         "time": 1700000000000, "date": "2024-01-01T00:00:00Z"},
        {"slug": "bitcoin", "priceUsd": "65000.00",
         "time": 1700003600000, "date": "2024-01-01T01:00:00Z"},
    ]