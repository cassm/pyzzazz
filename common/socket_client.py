import socket


class SocketClient:
    def __init__(self, port, host='127.0.0.1'):
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # now connect to the web server on port 80
        # - the normal http port
        self._socket.connect((host, port))
        print("SocketClient: connecting on {}:{}".format(host, port))

    def get_bytes(self):
        return self._socket.recv(4096)

    def close(self):
        self._socket.close()


sock = SocketClient(48945)

try:
    while True:
        bytes_recvd = sock.get_bytes()
        if len(bytes_recvd) > 0:
            print(bytes_recvd)
finally:
    sock.close()
