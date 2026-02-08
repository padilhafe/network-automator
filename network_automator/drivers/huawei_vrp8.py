def send_config(conn, config_set):
    """
    Envia configurações para dispositivos Huawei que requerem commit
    (como VRPv8) - Versão robusta com padrões de prompt flexíveis
    """
    import time

    # Captura o prompt original antes das mudanças
    original_prompt = conn.find_prompt()

    try:
        # Entra em system-view com comando direto e aguarda mudança de prompt
        config_output = "[INFO] Entrando em system-view...\n"

        # Envia system-view sem verificar padrão específico
        output = conn.send_command_timing("system-view", delay_factor=2)
        config_output += f"system-view\n{output}\n"
        time.sleep(2)

        # Aplica cada comando individualmente usando send_command_timing
        config_output += f"[INFO] Aplicando {len(config_set)} comandos...\n"

        for i, cmd in enumerate(config_set, 1):
            if cmd.strip():
                try:
                    # Usa send_command_timing que é mais confiável para VRP8
                    cmd_output = conn.send_command_timing(cmd, delay_factor=2)
                    config_output += f"[{i}] {cmd}\n{cmd_output}\n"
                    time.sleep(1)  # Delay entre comandos
                except Exception as e:
                    config_output += f"[{i}] {cmd}\n[WARNING] Erro: {str(e)}\n"

        # Executa commit usando send_command_timing para máxima compatibilidade
        config_output += "[INFO] Executando commit...\n"
        try:
            conn.send_command_timing("commit", delay_factor=4)
            config_output += "commit\n{commit_output}\n"
            config_output += "[INFO] Commit executado com sucesso\n"
        except Exception as e:
            config_output += f"commit\n[ERROR] Erro no commit: {str(e)}\n"

            # Fallback com send_command simples
            try:
                fallback_commit = conn.send_command("commit", read_timeout=20)
                config_output += f"[FALLBACK] Commit simples: {fallback_commit}\n"
            except Exception as e2:
                config_output += f"[ERROR] Commit fallback falhou: {str(e2)}\n"

        # Retorna ao modo usuário usando send_command_timing
        config_output += "[INFO] Retornando ao modo usuário...\n"
        try:
            return_output = conn.send_command_timing("return", delay_factor=2)
            config_output += f"return\n{return_output}\n"
            time.sleep(1)
        except Exception as e:
            config_output += f"[WARNING] Erro no return: {str(e)}\n"

        # Verifica mudança de hostname se aplicável
        if any("sysname" in cmd for cmd in config_set):
            time.sleep(3)
            try:
                new_prompt = conn.find_prompt()
                config_output += f"\n[INFO] Prompt: '{original_prompt.strip()}' → '{new_prompt.strip()}'\n"
            except Exception as e:
                config_output += (
                    f"\n[WARNING] Erro na detecção do novo prompt: {str(e)}\n"
                )

        config_output += "[INFO] Configuração VRP8 concluída\n"
        return config_output

    except Exception as e:
        error_msg = f"[ERROR] Erro geral na configuração VRP8: {str(e)}\n"
        error_msg += "[INFO] Tentando recuperação básica...\n"

        # Tentativa de recuperação básica
        try:
            conn.send_command_timing("return", delay_factor=1)
            error_msg += "[RECOVERY] Return executado\n"
        except Exception as e:
            print(f"Erro no comando: {e}")

        return error_msg
