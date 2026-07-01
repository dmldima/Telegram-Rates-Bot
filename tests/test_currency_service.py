"""Tests for currency rate resolution, with HTTP mocked out."""
import pytest
import services.currency_service as cs


@pytest.fixture(autouse=True)
def clear_cache():
    cs.clear_cache()
    yield
    cs.clear_cache()


def _mock_http(monkeypatch, responses):
    """Patch the HTTP helper. ``responses`` maps a URL substring -> json dict.
    Any URL not matched returns None (simulating 404/no data)."""
    async def fake(url, max_retries=cs.MAX_RETRIES):
        for needle, payload in responses.items():
            if needle in url:
                return payload
        return None
    monkeypatch.setattr(cs, "_http_json_with_retry", fake)


class TestMajorRate:
    async def test_direct_hit(self, monkeypatch):
        _mock_http(monkeypatch, {
            "2025-04-21": {"date": "2025-04-21", "rates": {"USD": 1.1}},
        })
        result = await cs.get_major_rate("EUR", "USD", "2025-04-21")
        assert result == (1.1, "2025-04-21", False)

    async def test_fallback_to_previous_date(self, monkeypatch):
        # Requested date has no data; the day before does.
        _mock_http(monkeypatch, {
            "2025-04-20": {"date": "2025-04-20", "rates": {"USD": 1.2}},
        })
        rate, actual_date, is_fallback = await cs.get_major_rate("EUR", "USD", "2025-04-21")
        assert rate == 1.2
        assert actual_date == "2025-04-20"
        assert is_fallback is True

    async def test_no_data_returns_none(self, monkeypatch):
        _mock_http(monkeypatch, {})
        assert await cs.get_major_rate("EUR", "USD", "2025-04-21") is None

    async def test_result_is_cached(self, monkeypatch):
        calls = {"n": 0}

        async def fake(url, max_retries=cs.MAX_RETRIES):
            calls["n"] += 1
            return {"date": "2025-04-21", "rates": {"USD": 1.1}}

        monkeypatch.setattr(cs, "_http_json_with_retry", fake)
        await cs.get_major_rate("EUR", "USD", "2025-04-21")
        await cs.get_major_rate("EUR", "USD", "2025-04-21")
        assert calls["n"] == 1  # second call served from cache


class TestUahRate:
    async def test_target_uah_direct(self, monkeypatch):
        # USD/UAH: NBU returns UAH per USD directly.
        _mock_http(monkeypatch, {
            "valcode=USD": [{"rate": 41.5, "exchangedate": "21.04.2025"}],
        })
        rate, actual_date, is_fallback = await cs.get_uah_rate("USD", "UAH", "2025-04-21")
        assert rate == 41.5
        assert actual_date == "2025-04-21"  # normalized from dd.mm.yyyy
        assert is_fallback is False

    async def test_base_uah_inverts(self, monkeypatch):
        # UAH/USD: invert NBU's UAH-per-USD rate.
        _mock_http(monkeypatch, {
            "valcode=USD": [{"rate": 40.0, "exchangedate": "21.04.2025"}],
        })
        rate, actual_date, is_fallback = await cs.get_uah_rate("UAH", "USD", "2025-04-21")
        assert rate == pytest.approx(1 / 40.0)

    async def test_no_data_returns_none(self, monkeypatch):
        _mock_http(monkeypatch, {})
        assert await cs.get_uah_rate("USD", "UAH", "2025-04-21") is None
