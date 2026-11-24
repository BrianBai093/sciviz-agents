"""External API service (Project 2): cache, key handling, budget, proxy. No network: a mock transport."""
import json
import urllib.error
import urllib.request

import httpx
import pytest

from sciviz.harness.openalex import ExternalBudgetExceeded, OpenAlexError, OpenAlexService, cache_key

KEY = "test-key-123"


def make_service(tmp_path, handler, budget=1.0):
    return OpenAlexService(KEY, tmp_path / "cache.sqlite", budget_usd=budget, rate_per_s=1000,
                           usage_path=tmp_path / "usage.json", transport=httpx.MockTransport(handler))


def ok_handler(calls):
    def handler(request: httpx.Request):
        calls.append(str(request.url))
        if request.url.params.get("filter") == "bad:1":
            return httpx.Response(400, text=f"Invalid query parameters for api_key={KEY}")
        return httpx.Response(200, json={"meta": {"count": 7}, "results": []},
                              headers={"x-ratelimit-cost-usd": "0.0001", "x-ratelimit-remaining-usd": "0.5"})
    return handler


def test_cache_key_ignores_key_and_order():
    assert cache_key("/works", {"b": 1, "a": 2, "api_key": "x"}) == cache_key("works", {"a": 2, "b": 1})


def test_second_identical_request_is_served_from_cache(tmp_path):
    calls = []
    svc = make_service(tmp_path, ok_handler(calls))
    a = svc.get("works", {"filter": "cites:W1", "per_page": 1})
    b = svc.get("works", {"per_page": 1, "filter": "cites:W1"})
    assert a == b and len(calls) == 1
    u = svc.usage_snapshot()
    assert u["requests"] == 1 and u["cache_hits"] == 1 and u["usd"] == pytest.approx(0.0001)
    assert u["daily_remaining_usd"] == 0.5
    assert all(f"api_key={KEY}" in c for c in calls)  # the key is added by the harness...
    svc.close()
    assert KEY not in (tmp_path / "usage.json").read_text()  # ...and never written anywhere


def test_errors_are_scrubbed_and_not_cached(tmp_path):
    calls = []
    svc = make_service(tmp_path, ok_handler(calls))
    with pytest.raises(OpenAlexError) as e:
        svc.get("works", {"filter": "bad:1"})
    assert KEY not in str(e.value) and "***" in str(e.value)
    with pytest.raises(OpenAlexError):
        svc.get("works", {"filter": "bad:1"})
    assert len(calls) == 2
    svc.close()


def test_only_entity_paths_are_allowed(tmp_path):
    svc = make_service(tmp_path, ok_handler([]))
    for bad in ("rate-limit", "works/../rate-limit", "https://evil.example/works"):
        with pytest.raises(ValueError):
            svc.get(bad)
    svc.close()


def test_session_budget_stops_paid_requests_but_not_cached_ones(tmp_path):
    svc = make_service(tmp_path, ok_handler([]), budget=0.0002)
    svc.get("works", {"filter": "cites:W1"})
    svc.get("works", {"filter": "cites:W2"})
    with pytest.raises(ExternalBudgetExceeded):
        svc.get("works", {"filter": "cites:W3"})
    assert svc.get("works", {"filter": "cites:W1"})["meta"]["count"] == 7
    svc.close()


def test_proxy_serves_kernels_without_the_key(tmp_path):
    svc = make_service(tmp_path, ok_handler([]))
    url = svc.start_proxy()
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    with opener.open(f"{url}/works?filter=cites:W9&per_page=1", timeout=10) as r:
        assert json.loads(r.read())["meta"]["count"] == 7
    with opener.open(f"{url}/__usage", timeout=10) as r:
        assert json.loads(r.read())["requests"] == 1
    with pytest.raises(urllib.error.HTTPError) as e:
        opener.open(f"{url}/rate-limit", timeout=10)
    assert e.value.code == 400
    svc.close()
