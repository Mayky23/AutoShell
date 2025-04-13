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
./AutoShell.sh [IP] [PUERTO]
./AutoShell.sh  # Modo interactivo
```
## 📋 Parámetros disponibles
| Parámetro    | Descripción                   | Valor por defecto | Ejemplo               |
|--------------|-------------------------------|:-----------------:|-----------------------|
| `IP`            | Dirección IP para escuchar    | 0.0.0.0           | 192.168.1.10          |
| `PUERTO`       | Puerto para escuchar          | 4444              | 5555                  |
| `-h, --help`   | Mostrar ayuda                 | N/A               | ./improved_shell.sh -h|

## 🌟 Ejemplos de uso
Ejemplo 1: Modo interactivo (sin parámetros)

```bash
$ ./AutoShell.sh

[*] Modo interactivo
Introduce IP [0.0.0.0]: 192.168.1.15
Introduce puerto [4444]: 5555

[*] Iniciando listener en 192.168.1.15:5555
[+] Conexión establecida desde 10.0.2.100:37842
[*] Mejorando shell...
[+] Shell mejorada con éxito!
user@victima:/$  # ¡Shell interactiva lista!
```
Ejemplo 2: Con parámetros directos

```bash
$ ./AutoShell.sh 0.0.0.0 4444

[+] Parámetros validados:
    - IP: 0.0.0.0
    - Puerto: 4444

[*] Iniciando listener...
[+] Conexión recibida desde [2001:db8::1]:41234
[*] Configurando TTY...
[+] TERM=xterm-256color
root@servidor:/home/admin#  # Prompt remoto
```

Ejemplo 3: Cuando falla la conexión
```bash
$ ./AutoShell.sh 192.168.1.20 8080

[*] Esperando conexión en 192.168.1.20:8080...
[!] Tiempo de espera agotado (15 segundos)
[!] No se recibieron conexiones
[*] Limpiando...
```
## 🛡 Características clave

✔️ Autodetección de Python/alternativas

✔️ Soporte para IPv4/IPv6

✔️ Validación de parámetros robusta

✔️ Limpieza automática de recursos

✔️ Configuración óptima de terminal

## ⚠️ Notas importantes
Requiere netcat instalado

Para problemas de terminal: ejecutar reset

Usar IP 0.0.0.0 para escuchar en todas las interfaces
