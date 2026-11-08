"""The ``>>>`` blocks of the documentation pages (docs/**/*.md) are doctests."""

import doctest
import re
from pathlib import Path

import pytest

DOCS = Path(__file__).resolve().parent.parent / "docs"
PAGES = sorted(p for p in DOCS.rglob("*.md") if "design" not in p.parts and ">>>" in p.read_text())
FENCE = re.compile(r"```python\n(.*?)```", re.S)


@pytest.mark.parametrize("page", PAGES, ids=[str(p.relative_to(DOCS)) for p in PAGES])
def test_page(page):
    text = "\n".join(b for b in FENCE.findall(page.read_text()) if b.lstrip().startswith(">>>"))
    parser = doctest.DocTestParser()
    test = parser.get_doctest(text, {}, str(page.relative_to(DOCS)), str(page), 0)
    runner = doctest.DocTestRunner(optionflags=doctest.ELLIPSIS | doctest.NORMALIZE_WHITESPACE)
    runner.run(test)
    assert runner.failures == 0, f"{runner.failures} failure(s) in {page.name}"


def test_doctests_found():
    assert PAGES
