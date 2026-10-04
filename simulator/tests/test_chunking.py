"""Tests for the chunking helper."""

from __future__ import annotations

import pytest

from app.utils.chunking import chunked


def test_chunked_splits_into_even_batches() -> None:
    assert list(chunked([1, 2, 3, 4], 2)) == [[1, 2], [3, 4]]


def test_chunked_keeps_remainder() -> None:
    assert list(chunked([1, 2, 3, 4, 5], 2)) == [[1, 2], [3, 4], [5]]


def test_chunked_empty_input() -> None:
    assert list(chunked([], 3)) == []


def test_chunked_rejects_non_positive_size() -> None:
    with pytest.raises(ValueError):
        list(chunked([1, 2, 3], 0))
