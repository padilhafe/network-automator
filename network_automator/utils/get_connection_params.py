import os

NETMIKO_KEYS = {
    "host",
    "username",
    "password",
    "secret",
    "device_type",
    "port",
    "ssh_config_file",
    "use_keys",
    "key_file",
    "allow_agent",
    "timeout",
    "conn_timeout",
    "auth_timeout",
    "session_log",
}


def get_connection_params(device: dict) -> dict:
    params = {k: v for k, v in device.items() if k in NETMIKO_KEYS}

    # Handle configurable log path
    if "session_log" in params and "log_path" in device:
        log_path = device["log_path"]
        log_file = params["session_log"]

        # Create log directory if it doesn't exist
        if log_path and not os.path.exists(log_path):
            os.makedirs(log_path, exist_ok=True)

        # Combine log path with log file
        if log_path:
            params["session_log"] = os.path.join(log_path, log_file)

    return params
