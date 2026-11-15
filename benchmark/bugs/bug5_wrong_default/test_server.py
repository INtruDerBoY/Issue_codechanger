from constants import DEFAULT_PORT
from server import get_server_config


def test_default_port_is_8080():
    cfg = get_server_config()
    assert cfg["port"] == DEFAULT_PORT
