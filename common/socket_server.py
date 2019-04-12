import socket
import select
import errno


class SocketServer:
    class ClientsInfo:
        def __init__(self, num_writeable, num_readable, num_errored):
            self.num_writeable = num_writeable
            self.num_readable = num_readable
            self.num_errored = num_errored

    def __init__(self, port, host='127.0.0.1'):
        self._server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._server_socket.bind((host, port))
        self._server_socket.listen()

        print("SocketServer: listening on {}:{}".format(host, port))

        self.send_buffer = bytearray()
        self._read_list = [self._server_socket]
        self._write_list = []

    def send_bytes(self, bytes):
        # only send if we have a client
        if len(self._write_list) > 0:
            if len(self.send_buffer) == 0:
                self.send_buffer = bytes
            else:
                self.send_buffer.extend(bytes)

    def poll(self):
        readable, writeable, errored = select.select(self._read_list, self._write_list, [], 0.5)

        for s in readable:
            if s is self._server_socket:
                client_socket, address = self._server_socket.accept()
                self._write_list.append(client_socket)
                print("Connection from {}".format(address))

        for s in writeable:
            if len(self.send_buffer) > 0:
                try:
                    sent = s.send(self.send_buffer)
                    self.send_buffer = self.send_buffer[sent:]
                    print("Sent {} bytes".format(sent))

                except socket.error as e:
                    if e.errno != errno.EAGAIN:
                        s.close()
                        self._write_list.remove(s)

                        raise e

                    print('Blocking with', len(self.send_buffer), 'remaining')

        for s in errored:
            print("closing errored socket ()".format(s))
            self._read_list.remove(s)
            self._write_list.remove(s)
            s.close()
