import socket
import select
import threading
import client


class Server(object):
    def __init__(self, port, host='localhost'):
        self.port = port
        self.host = host
        self.running = True
        self.exit_request = False
        self.clients = []

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setblocking(0)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind((self.host, self.port))

        self.thread = ServerThread(self)
        self.thread.start()

    def disconnect_all(self):
        for cli in self.clients:
            cli.disconnect()
            while cli.connected:
                pass

    def close(self):
        self.exit_request = True
        while self.running:
            pass


class ServerThread(threading.Thread):
    def __init__(self, parent):
        super(ServerThread, self).__init__()
        self.parent = parent

    def run(self):
        self.parent.socket.listen(1)
        while not self.parent.exit_request:
            ready_to_read, ready_to_write, in_error = select.select(
                [self.parent.socket], [], [], 2
            )
            if self.parent.socket not in ready_to_read:
                continue

            client_socket, address = self.parent.socket.accept()
            self.parent.clients.append(client.Client(client_socket, address, self.parent))

        self.parent.socket.close()
        self.parent.disconnect_all()
        self.parent.running = False




