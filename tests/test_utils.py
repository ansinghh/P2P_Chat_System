import pytest
from p2pchat.client import get_chat_key

def test_get_chat_key_consistency():
    key1 = get_chat_key('alice', 'bob')
    key2 = get_chat_key('bob', 'alice')
    assert key1 == key2, "Chat key should be the same regardless of user order"

def test_get_chat_key_length():
    key = get_chat_key('alice', 'bob')
    assert len(key) > 0, "Generated key should not be empty"