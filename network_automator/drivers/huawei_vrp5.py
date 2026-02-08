def send_config(conn, config_set):
    """
    Envia configurações para dispositivos Huawei que NÃO requerem commit
    (como VRP 5)
    """
    import time

    # Captura o prompt original antes das mudanças
    original_prompt = conn.find_prompt()

    try:
        # Usa send_config_set com timeouts mais generosos
        output = conn.send_config_set(config_set, read_timeout=15, cmd_verify=False)

        # Se o hostname foi alterado, o prompt mudou, então refaz a detecção
        if any("sysname" in cmd for cmd in config_set):
            time.sleep(2)

            # Força nova detecção do prompt
            try:
                new_prompt = conn.find_prompt()
                output += f"\n[INFO] Prompt alterado de '{original_prompt.strip()}' para '{new_prompt.strip()}'"
            except Exception as e:
                output += f"\n[WARNING] Erro na detecção do novo prompt: {str(e)}"

        # Salva configuração automaticamente (VRP5 salva automaticamente)
        try:
            save_output = conn.send_command(
                "save", expect_string=r"[Yy]\/[Nn]", read_timeout=10
            )
            if "[Y/N]" in save_output or "[y/n]" in save_output:
                final_save = conn.send_command("Y", read_timeout=10)
                output += f"\n[INFO] Configuração salva: {final_save.strip()}"
        except Exception as e:
            output += f"\n[WARNING] Erro ao salvar configuração: {str(e)}"

        return output

    except Exception as e:
        return f"[ERROR] Erro na configuração VRP5: {str(e)}"
