# AutoShell 🚀

Herramienta para automatizar la mejora de shells inversas a TTY completamente interactivas con detección inteligente de entornos.

## 📦 Instalación

```bash
git clone https://github.com//Mayky23/AutoShell.git
cd AutoShell
chmod +x AutoShell.py
```

## 🛠 Uso básico

```bash
./AutoShell.py <puerto>
```

## 🌟 Ejemplo de uso

```bash
$ ./AutoShell.py 4444
[*] Escuchando en 0.0.0.0:4444...
[+] Conexión de 10.0.2.15:44866
[*] Shell activa

# COMANDOS EJECUTADOS AUTOMATICAMANTE 
usuario@debian:~$ python -c "import pty; pty.spawn('/bin/bash')"
usuario@debian:~$ python3 -c "import pty; pty.spawn('/bin/bash')"
usuario@debian:~$ echo "stty raw -echo; fg" > /tmp/.stab && chmod +x /tmp/.stab
usuario@debian:~$ export TERM=xterm-256color
usuario@debian:~$ stty rows 40 columns 180

# SHELL COMPLETAMENTE INTERACTIVA
usuario@debian:~$ 
```
