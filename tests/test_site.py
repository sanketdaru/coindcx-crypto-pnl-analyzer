"""The landing page carries the SEO payload; these assert it stays intact."""

import json
import re
from pathlib import Path

import pytest

SITE = Path(__file__).resolve().parents[1] / 'site'
INDEX = SITE / 'index.html'
CANONICAL = 'https://sanketdaru.github.io/india-crypto-tax-calculator/'


@pytest.fixture(scope='module')
def html() -> str:
    return INDEX.read_text(encoding='utf-8')


def _json_ld_blocks(html: str):
    pattern = re.compile(
        r'<script[^>]+type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',
        re.DOTALL | re.IGNORECASE,
    )
    return [json.loads(m.group(1)) for m in pattern.finditer(html)]


def test_site_files_exist():
    for name in ('index.html', 'robots.txt', 'sitemap.xml'):
        assert (SITE / name).is_file(), f'missing site/{name}'


def test_title_is_present_and_reasonably_sized(html):
    match = re.search(r'<title>(.*?)</title>', html, re.DOTALL)
    assert match, 'no <title>'
    title = match.group(1).strip()
    assert 'Crypto Tax' in title
    assert len(title) <= 65, f'title too long for search results: {len(title)}'


def test_meta_description_is_present_and_within_snippet_length(html):
    match = re.search(
        r'<meta\s+name=["\']description["\']\s+content=["\'](.*?)["\']', html, re.DOTALL
    )
    assert match, 'no meta description'
    description = match.group(1).strip()
    assert 50 <= len(description) <= 160, f'description length {len(description)}'


def test_canonical_url_is_correct(html):
    assert f'<link rel="canonical" href="{CANONICAL}"' in html


def test_open_graph_and_twitter_cards_present(html):
    for tag in ('og:title', 'og:description', 'og:url', 'og:type', 'twitter:card'):
        assert tag in html, f'missing {tag}'


def test_json_ld_blocks_are_valid_json(html):
    blocks = _json_ld_blocks(html)
    assert len(blocks) >= 2, 'expected SoftwareApplication and FAQPage blocks'
    for block in blocks:
        assert block.get('@context') == 'https://schema.org'
        assert '@type' in block


def test_software_application_schema(html):
    app = next(b for b in _json_ld_blocks(html) if b['@type'] == 'SoftwareApplication')
    assert app['applicationCategory'] == 'FinanceApplication'
    assert app['offers']['price'] == '0'
    assert app['license'].endswith('Apache-2.0')


def test_faq_schema_answers_are_not_empty(html):
    faq = next(b for b in _json_ld_blocks(html) if b['@type'] == 'FAQPage')
    assert len(faq['mainEntity']) >= 6, 'FAQ schema is the main SEO lever; keep it substantial'
    for entry in faq['mainEntity']:
        assert entry['@type'] == 'Question'
        assert entry['name'].strip()
        assert len(entry['acceptedAnswer']['text'].strip()) > 40


def test_page_is_self_contained(html):
    """No CDN, no external fonts, no remote images, no analytics."""
    remote = re.findall(r'(?:src|href)=["\'](https?://[^"\']+)["\']', html)
    allowed_prefixes = (CANONICAL, 'https://github.com/sanketdaru/', 'https://schema.org')
    for url in remote:
        assert url.startswith(allowed_prefixes), f'external asset or link not allowed: {url}'


def test_disclaimer_appears_above_the_fold(html):
    body = html[html.index('<body'):]
    assert 'NOT TAX ADVICE' in body.upper()
    # It must come before the feature copy, not be buried in a footer.
    assert body.upper().index('NOT TAX ADVICE') < body.index('id="install"')


def test_sitemap_lists_the_canonical_url():
    sitemap = (SITE / 'sitemap.xml').read_text(encoding='utf-8')
    assert CANONICAL in sitemap


def test_robots_allows_crawling_and_points_to_sitemap():
    robots = (SITE / 'robots.txt').read_text(encoding='utf-8')
    assert 'Disallow:\n' in robots or 'Disallow: \n' in robots or 'Allow: /' in robots
    assert 'sitemap.xml' in robots.lower()
