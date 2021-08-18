
import pytest
from dcc_phi_reporter.app import utf8len, chunk_split



def test_determine_byte_size():
    a = 'The quick brown fox jumps over the lazy dog'
    expected = 43
    assert utf8len(a) == expected


def test_chunk_split():
    a = 'The quick brown fox jumps over the lazy dog'
    # b = b'The quick brown fox jumps over the lazy dog'
    # chunks = chunk_split(a, chunk_size=5)
    # expected = 9
    chunks = chunk_split(a, chunk_size=500)
    expected = 1
    print(chunks)
    print(bytes(a, 'utf-8'))
    print(bytes(a, 'utf-16'))
    assert len(chunks) == expected
