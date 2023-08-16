import argparse
import logging
import math
import os
import socket
from threading import Thread

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


class ServerManager(Thread):
    max_empty_data: int = 10

    def __init__(self, connection, host: str, port: int):
        """
        :param connection: Communication channel opened by the client
        :param host: Server host
        :param port: Server post
        """
        Thread.__init__(self)
        self.host: str = host
        self.port: int = port
        self.conn = connection

        # Contain information about the operation being carried out with the customer
        self.action = None
        self.filename = None
        self.size = 0

        # Variable used for correct reception (without loss of information) of files
        self.share_in_progress: bool = False  # Determines whether file sharing is in progress
        self.total_recv: int = 0   # Total size of data to be received
        self.current_recv: int = 0  # Size of data already received
        self.shared_data: bytes = b''  # Received data
        self.successive_empty_data: int = 0

    @property
    def base_dir(self) -> str:
        """
        :return: Server data location (root /)
        """
        directory = os.path.join(os.path.dirname(__file__), "storage")

        if not os.path.exists(directory) or not os.path.isdir(directory):
            os.mkdir(directory)

        return directory

    def run(self):
        logging.info("[+] New connected client " + self.host + ":" + str(self.port))

        while True:
            # We get a message from the client
            data: bytes = self.conn.recv(2048)

            if not self.share_in_progress:
                if data != b'':
                    logging.info(f"[*] The server has received data from client")
                    self.successive_empty_data = 0
                else:
                    if self.successive_empty_data >= self.max_empty_data:
                        self.conn.close()
                        break
                    self.successive_empty_data += 1
            else:
                logging.info(f"[*] Receiving a file in progress { ((self.current_recv + 1) / self.total_recv) * 100 }%")

            if self.share_in_progress:  # A file is being received on the server side.
                if self.action == 1:
                    self.shared_data += data
                    self.current_recv += 1

                    if self.current_recv >= self.total_recv:
                        # File uploaded to server
                        self.share_in_progress = False
                        self.current_recv = 0
                        self.total_recv = 0
                        self._receive_file(self.shared_data)
                        self.shared_data = b''
                        logging.info(f"[*] The file { self.filename } has been uploaded to the server")

            elif self.action is None and self.filename is None:
                # We determine the operation requested by the client
                try:
                    content = data.decode("utf-8").split("++")
                    self.action = int(content[1])
                    self.filename = content[2]

                    if self.action == 1:  # This is a file transfer from the client to the server.
                        self.size = int(content[3])  # We retrieve the size of the file to be uploaded to the server.

                except (UnicodeError, ValueError, IndexError):
                    self.conn.send("abort".encode("utf-8"))
                else:
                    if self.filename == "exit":
                        self.conn.close()
                        break
                    else:
                        self.filename = os.path.join(self.base_dir, self.filename)

                        if self.action == 2:
                            # File transfer from server to client
                            if os.path.exists(self.filename) and os.path.isfile(self.filename):
                                self.conn.send("ok".encode("utf-8"))  # The desired file is available on the server
                                # Sends the size of the file to be downloaded to the client
                                self.conn.send(f"{ os.path.getsize(self.filename) }".encode("utf-8"))
                                self._send_file()  # Send file
                            else:
                                # File not found
                                self.conn.send("abort".encode("utf-8"))
                        else:
                            # File transfer from client to server
                            self.share_in_progress = True
                            self.total_recv = math.ceil(self.size / 2048)
                            self.current_recv = 0
                            self.conn.send("ok".encode("utf-8"))

        logging.info(f"[-] Client disconnected : { self.conn }")

    def _send_file(self) -> None:
        """ Send a file """
        with open(self.filename, "rb") as file:
            self.conn.send(file.read())
            file.close()

        logging.info(f"[*] The { self.filename } file has been sent")

        self.action = None
        self.filename = None

    def _receive_file(self, data: bytes) -> None:
        """ Receiving and saving a file """
        try:
            data = data.decode("utf-8")
        except UnicodeError:
            file = open(self.filename, "wb")
        else:
            file = open(self.filename, "w")

        file.write(data)
        file.close()

        logging.info(f"[*] The file { self.filename } has been received")

        self.conn.send("ok".encode("utf-8"))
        self.action = None
        self.filename = None


class TCPServer:
    def __init__(self, host: str, port: int):
        """
        :param host: Server host
        :param port: Server port
        """
        self.host: str = host
        self.port: int = port
        self.socket = None

    def start(self):
        """ Start running server """
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind((self.host, self.port))

        logging.info("[i] Server started")

        # Infinite loop to keep server active (prevents program and server from stopping)
        while True:
            self.socket.listen(10)
            logging.info("[i] Server: waiting for TCP client connections ...")
            (con, (ip, port)) = self.socket.accept()  # A new client is connected
            # Launch an asynchronous class to communicate with the client without locking the server's listening port.
            ServerManager(con, ip, port).start()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-s', '--host', type=str, help='Server host', required=True)
    parser.add_argument('-p', '--port', type=int, help='Server port', required=True)

    # Analyze arguments
    args = parser.parse_args()

    # Start server
    TCPServer(host=args.host, port=args.port).start()
