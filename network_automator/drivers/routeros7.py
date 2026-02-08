def send_config(conn, config_set):
    return conn.send_config_set(config_set, exit_config_mode=False)
