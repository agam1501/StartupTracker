"""Verify optional dependencies are properly installed."""


def test_rapidfuzz_importable():
    import rapidfuzz.fuzz  # noqa: F401


def test_trafilatura_importable():
    import trafilatura  # noqa: F401
