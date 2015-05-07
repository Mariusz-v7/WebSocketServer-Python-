import threading
import select
import re
import hashlib
import base64
import lowlewel


class Client(object):
    def __init__(self, sock, address, host):
        self.socket = sock
        self.socket.setblocking(0)
        self.server = host
        self.address = address
        self.connected = True
        self.exit_request = False
        self.handshake_start = False
        self.handshake_completed = False

        #
        self.thread = ClientThread(self)
        self.thread.start()

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
        data = str(data)
        if not self.handshake_completed:
            lines = data.split('\n')
            for command in lines:
                self.handshake(command)
        else:
            self.data_from_websocket(self.unmask(data))

    def unmask(self, payload):
        length = ord(payload[1]) & 0x7F

        if length <= 125:
            maskkey = payload[2:7]
            data = payload[6:]
            data = data[:length]
        elif length == 126: #length field is next two bytes
            lenbytes = []
            for i in range(0, 2):
                lenbytes.append(ord(payload[2 + i]))
            length = lowlewel.multibyteval(lenbytes) # new length
            maskkey = payload[4:9]
            data = payload[8:]
            data = data[:length]
        elif length == 127: #length field is next 8 bytes
            lenbytes = []
            for i in range(0, 8):
                lenbytes.append(ord(payload[2 + i]))
            length = lowlewel.multibyteval(lenbytes) # new length
            maskkey = payload[10:15]
            data = payload[14:]
            data = data[:length]

        text = ''
        for i, c in enumerate(data):
            text += chr(ord(c) ^ ord(maskkey[i % 4]))

        return text

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

        self.parent.send('Bye!')
        self.parent.socket.close()
        self.parent.connected = False
