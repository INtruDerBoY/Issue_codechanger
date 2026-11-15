from constants import DEFAULT_PORT, DEFAULT_TIMEOUT


# Bug: defaults port to 80 instead of DEFAULT_PORT
def get_server_config(port: int = 80, timeout: int = DEFAULT_TIMEOUT) -> dict:
    return {"port": port, "timeout": timeout}
