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


def test_readme_examples():
    """The Python blocks of the README run (the first one: a 4-thread simulation, a few seconds)."""
    readme = DOCS.parent / "README.md"
    blocks = [b for b in FENCE.findall(readme.read_text()) if not b.lstrip().startswith(">>>")]
    assert len(blocks) >= 2
    ns: dict = {}
    for block in blocks:
        exec(compile(block, str(readme), "exec"), ns)  # noqa: S102 (the README of the repository)
    assert ns["mnt"].n_fe >= 100 and 0 < ns["mnt"].fer < 0.05  # CA-SCL (128, 64) at 3 dB
    assert (ns["cdc"].encoder.K, ns["cdc"].puncturer.N) == (2048, 4108)
