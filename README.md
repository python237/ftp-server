# Ftp-Server
---
It's a mini client-server for sharing files of all types and sizes.
The server must first be started with the command
```
python3 server.py -s localhost -p 9999
```

where
- **(-s)** : determines the server's ip address
- **(-p)** : determines the port to be used for connection

> **Important note:** 
> 
> If you're running the server on a remote machine, make sure you've opened the port in your firewall to accept connections.

---

Once the server has been started, any client can connect to the server and perform 2 actions:
- *Send a file to the server (so that it can be stored)*
- *Download a file from the server.*

The command to enter is :
```
python3 client.py -s localhost -p 9999 -a u -f /home/python237/Desktop/lala.mp4
```

where
- **(-s)** : determines the server's ip address
- **(-p)** : determines the port to use for connection
- **(-a)** : determines the action to be performed. either "u" to send a file or "d" to download a file.
- **(-f)** : determines the file to send/receive.
