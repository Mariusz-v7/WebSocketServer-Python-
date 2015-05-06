import threading
import select


class Client(object):
    def __init__(self, sock, address, host):
        self.socket = sock
        self.server = host
        self.address = address
        self.connected = True
        self.exit_request = False

        self.thread = ClientThread(self)
        self.thread.start()

        self.socket.setblocking(0)

    def disconnect(self):
        self.exit_request = True


class ClientThread(threading.Thread):
    def __init__(self, parent):
        super(ClientThread, self).__init__()
        self.parent = parent

    def run(self):
        while not self.parent.exit_request:
            ready_to_read, ready_to_write, in_error = select.select(
                [self.parent.socket], [], [], 2
            )
            if self.parent.socket not in ready_to_read:
                continue
            data = self.parent.socket.recv(1024)
            if not data:
                break
            self.parent.socket.sendall(data)

        self.parent.socket.sendall('Bye!')
        self.parent.socket.close()
        self.parent.connected = False
