"""Offline tests for the eBay search-result parsing logic.

These use hand-built HTML fixtures so the dual-layout parser can be validated
without making live requests to eBay. Run with:

    python tests/test_parse.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import bot  # noqa: E402


S_CARD_HTML = """
<html><body><ul>
  <li class="s-card">
    <div class="s-card__title">Shop on eBay</div>
    <span class="s-card__price">$0.99</span>
    <a href="https://www.ebay.com/itm/123456?hash=placeholder">x</a>
    <img src="https://i.ebayimg.com/images/g/aaa/s-l225.jpg">
  </li>
  <li class="s-card">
    <div class="s-card__title">Pokemon Charizard Holo PSA 9<span class="clipped">Opens in a new window or tab</span></div>
    <span class="s-card__price">$450.00</span>
    <a href="https://www.ebay.com/itm/111222333?epid=9&hash=xyz">x</a>
    <img src="https://i.ebayimg.com/images/g/bbb/s-l225.jpg">
  </li>
  <li class="s-card">
    <div class="s-card__title">Charizard Base Set Unlimited</div>
    <span class="s-card__price">$320.50</span>
    <a href="https://www.ebay.com/itm/444555666">x</a>
    <img data-src="https://i.ebayimg.com/images/g/ccc/s-l225.jpg">
  </li>
</ul></body></html>
"""

S_ITEM_HTML = """
<html><body><ul>
  <li class="s-item">
    <div class="s-item__title">Shop on eBay</div>
    <span class="s-item__price">$20.00</span>
    <a class="s-item__link" href="https://www.ebay.com/itm/000000?hash=ph">x</a>
  </li>
  <li class="s-item">
    <div class="s-item__title">Charizard 1st Edition Shadowless</div>
    <span class="s-item__price">$1,200.00</span>
    <a class="s-item__link" href="https://www.ebay.com/itm/777888999?hash=a">x</a>
    <img class="s-item__image-img" src="https://i.ebayimg.com/images/g/ddd/s-l225.jpg">
  </li>
  <li class="s-item">
    <div class="s-item__title">Charizard GX Rainbow Rare</div>
    <span class="s-item__price">$95.00</span>
    <a class="s-item__link" href="https://www.ebay.com/itm/555444333">x</a>
  </li>
</ul></body></html>
"""

BLOCK_HTML = "<html><body><h1>Pardon Our Interruption...</h1></body></html>"


def test_s_card_layout():
    items = bot.parse_search_html(S_CARD_HTML)
    assert len(items) == 2, items
    assert items[0]["title"] == "Pokemon Charizard Holo PSA 9"
    assert items[0]["price"] == "$450.00"
    assert items[0]["link"] == "https://www.ebay.com/itm/111222333"  # query stripped
    assert items[0]["image"] == "https://i.ebayimg.com/images/g/bbb/s-l225.jpg"
    # Image pulled from data-src when src is absent.
    assert items[1]["image"] == "https://i.ebayimg.com/images/g/ccc/s-l225.jpg"


def test_s_item_layout():
    items = bot.parse_search_html(S_ITEM_HTML)
    assert len(items) == 2, items
    assert items[0]["title"] == "Charizard 1st Edition Shadowless"
    assert items[0]["price"] == "$1,200.00"
    assert items[0]["link"] == "https://www.ebay.com/itm/777888999"
    # No image on the second card -> None (og:image fallback would fill it live).
    assert items[1]["image"] is None


def test_placeholder_is_skipped():
    for html in (S_CARD_HTML, S_ITEM_HTML):
        titles = [item["title"] for item in bot.parse_search_html(html)]
        assert "Shop on eBay" not in titles


def test_max_results_cap():
    cards = "".join(
        f'<li class="s-card"><div class="s-card__title">Item {n}</div>'
        f'<span class="s-card__price">${n}.00</span>'
        f'<a href="https://www.ebay.com/itm/{n}00">x</a></li>'
        for n in range(1, 6)
    )
    items = bot.parse_search_html(f"<ul>{cards}</ul>")
    assert len(items) == bot.MAX_RESULTS


def test_no_results():
    assert bot.parse_search_html("<html><body>nothing here</body></html>") == []


def test_block_detection():
    assert bot._looks_blocked(BLOCK_HTML) is True
    assert bot._looks_blocked("<html>normal results page</html>") is False


def test_clean_title_strips_accessibility_text():
    assert bot._clean_title("Charizard PSA 9Opens in a new window or tab") == "Charizard PSA 9"
    assert bot._clean_title("New ListingCharizard Holo") == "Charizard Holo"
    assert bot._clean_title("  Plain Title  ") == "Plain Title"


class _FakeResponse:
    def __init__(self, status_code, text):
        self.status_code = status_code
        self.text = text


class _FakeSession:
    """Serves queued responses for the search URL (repeating the last) to simulate retries.

    The homepage warm-up request always returns 200 and does not consume a queued response,
    so `calls` counts only the search requests.
    """

    def __init__(self, responses):
        self._responses = list(responses)
        self.calls = 0

    def get(self, url, *args, **kwargs):
        if url == bot.EBAY_HOME_URL:
            return _FakeResponse(200, "")
        resp = self._responses[min(self.calls, len(self._responses) - 1)]
        self.calls += 1
        return resp


def test_retry_recovers_after_blocked_ip():
    # First attempt gets a 403 (flagged proxy IP), retry lands a good IP.
    fake = _FakeSession([_FakeResponse(403, ""), _FakeResponse(200, S_CARD_HTML)])
    orig_build, orig_img = bot._build_session, bot.get_high_res_image
    bot._build_session = lambda: fake
    bot.get_high_res_image = lambda session, url: None
    try:
        result = bot.get_sold_items("charizard")
    finally:
        bot._build_session, bot.get_high_res_image = orig_build, orig_img
    assert isinstance(result, list) and len(result) == 2, result
    assert fake.calls == 2


def test_gives_up_after_max_attempts():
    fake = _FakeSession([_FakeResponse(403, "")])  # always blocked
    orig_build = bot._build_session
    bot._build_session = lambda: fake
    try:
        result = bot.get_sold_items("charizard")
    finally:
        bot._build_session = orig_build
    assert isinstance(result, dict) and "error" in result, result
    assert fake.calls == bot.EBAY_MAX_ATTEMPTS


def _run():
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    failures = 0
    for test in tests:
        try:
            test()
            print(f"PASS {test.__name__}")
        except AssertionError as exc:
            failures += 1
            print(f"FAIL {test.__name__}: {exc}")
    print(f"\n{len(tests) - failures}/{len(tests)} passed")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(_run())
