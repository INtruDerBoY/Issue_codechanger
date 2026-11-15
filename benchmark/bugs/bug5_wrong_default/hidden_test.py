from constants import DEFAULT_TIMEOUT
from server import get_server_config


def test_custom_port_override():
    cfg = get_server_config(port=9000)
    assert cfg["port"] == 9000
    assert cfg["timeout"] == DEFAULT_TIMEOUT
