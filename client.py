import threading
import select
import re
import hashlib
import base64


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

        self.handshake_start = False
        self.handshake_completed = False

    def handshake(self, command):
        if not self.handshake_start:
            check = re.match('GET', command)
            if check:
                self.handshake_start = True
        else:
            check = re.match(r'Sec-WebSocket-Key: (.*?)$', command, re.M | re.I)
            if check:
                wskey = str(check.group(1)).strip()
                wskey += str('258EAFA5-E914-47DA-95CA-C5AB0DC85B11')

                response_code = base64.b64encode(hashlib.sha1(wskey).digest())

                response = 'HTTP/1.1 101 Switching Protocols\r\n'
                response += 'Upgrade: websocket\r\n'
                response += 'Connection: Upgrade\r\n'
                response += 'Sec-WebSocket-Accept: '+response_code+'\r\n'
                response += '\r\n'

                self.send(response)
                self.handshake_start = False
                self.handshake_completed = True

    def on_receive(self, data):
        if not self.handshake_completed:
            lines = data.split('\n')
            for command in lines:
                self.handshake(command)
        else:
            self.data_from_websocket(data)

    def data_from_websocket(self, data):
        print 'ws: ', data

    def send(self, data):
        self.socket.sendall(data)

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
            self.parent.on_receive(data)

        self.parent.socket.sendall('Bye!')
        self.parent.socket.close()
        self.parent.connected = False
