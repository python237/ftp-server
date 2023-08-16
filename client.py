import argparse
import logging
import math
import os
import socket

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


class TCPClient:
    def __init__(self, host: str, port: int):
        """
        :param host: Server host
        :param port: Server port
        """
        self.host: str = host
        self.port: int = port
        self.socket = None

    def _connect(self) -> None:
        """ Connects to the server """
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((self.host, self.port))
        logging.info(f"[i] Successful connection to server { self.host }:{ self.port }")

    def _disconnect(self) -> None:
        """ Disconnects from server """
        if self.socket is not None:
            self.socket.send(f"RR***Great++1++exit++***".encode())
            self.socket.close()
            logging.info(f"[i] Successful server disconnection { self.host }:{ self.port }")

    def upload_file(self, filepath: str) -> None:
        """
        Send file to server
        :param filepath: The location of the file to be sent (absolute path)
        :return:
        """
        if os.path.exists(filepath) and os.path.isfile(filepath):
            self._connect()
            logging.info(f"[i] Send { filepath } file")
            was_sent = False

            with open(filepath, "rb") as file:
                self.socket.send(
                    f"RR***Great++1++{ os.path.basename(filepath).replace('++', '!!?') }"
                    f"++{ os.path.getsize(filepath) }++***".encode()
                )
                response = self.socket.recv(2048).decode("utf-8")

                if response == "ok":
                    self.socket.send(file.read())  # File upload
                    # Waiting for confirmation of receipt from the server
                    was_sent = self.socket.recv(2048).decode("utf-8") == "ok"

                file.close()

            if was_sent:
                logging.info(f"[i] The file has been sent!")
            else:
                logging.info(f"[!] The file has not been sent!")

            self._disconnect()
        else:
            logging.info(f"[!] The file { filepath } cannot be found")

    def download_file(self, filename: str) -> None:
        """
        Download a file from the server
        :param filename: The name of the file to download
        :return:
        """
        self._connect()
        self.socket.send(f"RR***Great++2++{filename.replace('++', '!!?')}++***".encode())
        response = self.socket.recv(2048).decode("utf-8")

        if response == "ok":
            # The server confirms the presence of this file in its directory
            logging.info(f"[i] Start downloading the { filename } file")

            size = int(self.socket.recv(2048).decode("utf-8"))  # Recover file size
            index = 0
            bytes_content = b''

            # Since packets are sent in batches (max. 2048 bytes per transfer),
            # we set up a loop that stops only when the file has been completely downloaded.
            while index < math.ceil(size / 2048):
                progress = ((index + 1) / math.ceil(size / 2048)) * 100

                if (int(progress) % 10) == 0:
                    logging.info(f"[i] Download in progress { progress }%")

                bytes_content = bytes_content + self.socket.recv(2048)
                index += 1

            # Rename filename in local if file already exist
            while os.path.exists(filename):
                filename = f"(1) {filename}"

            try:
                bytes_content = bytes_content.decode("utf-8")
            except UnicodeError:
                file = open(filename, "wb")
            else:
                file = open(filename, "w")

            file.write(bytes_content)  # Saving the file on the client machine
            file.close()

            logging.info(f"[i] The file has been downloaded successfully. output : {filename}")
        else:
            print(f"[!] The { filename } file cannot be found on the server")

        self._disconnect()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-s', '--host', type=str, help='Server host', required=True)
    parser.add_argument('-p', '--port', type=int, help='Server port', required=True)
    parser.add_argument(
        '-a',
        '--action',
        type=str,
        choices=["u", "d"],
        help='Action ("u" for upload, "d" for download)',
        required=True
    )
    parser.add_argument('-f', '--file', type=str, help='Filename|Filepath', required=True)

    # Analyze arguments
    args = parser.parse_args()

    client = TCPClient(host=args.host, port=args.port)

    if args.action == "u":
        client.upload_file(args.file)
    else:
        client.download_file(args.file)
