import pytest

from src.evidencetrail.agent import Source, canonical_url, deduplicate, validate_citations


def test_deduplicate_preserves_original_url_and_queries():
    first = Source(title="A", url="https://example.org/page?utm_source=search", content="Short", queries=["one"])
    second = Source(title="A", url="https://example.org/page", content="Longer content", queries=["two"])
    result = deduplicate([first, second])
    assert len(result) == 1
    assert result[0].url == first.url
    assert result[0].content == "Longer content"
    assert result[0].queries == ["one", "two"]
    assert canonical_url(first.url) == canonical_url(second.url)


def test_rejects_fabricated_citation():
    sources = [Source(id="S1", title="A", url="https://example.org/", content="x")]
    with pytest.raises(ValueError, match="fabricated"):
        validate_citations("Claim [S2]", sources)
    with pytest.raises(ValueError, match="no source citations"):
        validate_citations("Unsupported claim", sources)
    validate_citations("Supported claim [S1]", sources)
