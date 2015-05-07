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
        self.buffer = bytearray()

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

                self.send_raw(response)
                self.handshake_start = False
                self.handshake_completed = True

    def on_receive(self, data):
        for byte in data:
            self.buffer.append(byte)
        self.parse_buffer()

    def parse_buffer(self):
        if not self.handshake_completed:
            command = ''
            for byte in self.buffer:
                if chr(byte) == '\n':
                    self.handshake(command)
                    for k in command:
                        self.buffer.pop(0)
                    self.buffer.pop(0)

                    self.parse_buffer()
                    return
                command += chr(byte)
        else:
            while len(self.buffer) > 0 and self.buffer[0] & (~0x80) != 0x01:
                self.buffer.pop(0)

            if len(self.buffer) > 0:
                self.parse_frame()

    def parse_frame(self):
        length = self.get_frame_length(self.buffer)

        if not length:  # buffer too short
            return

        if length <= len(self.buffer):
            data = self.unmask(self.buffer)
            if not data:
                return

            for i in range(0, length):
                self.buffer.pop(0)

            self.data_from_websocket(data)
            self.parse_buffer()
        else:  # buffer too short - wait until next data come
            return

    def get_frame_length(self, payload):
        try:
            length = payload[1] & 0x7F

            if length == 126:  # length field is next two bytes
                lenbytes = []
                for i in range(0, 2):
                    lenbytes.append(payload[2 + i])
                length = lowlewel.multibyteval(lenbytes)
                length += 2  # 2 bytes of length value
            elif length == 127:  # length field is next 8 bytes
                lenbytes = []
                for i in range(0, 8):
                    lenbytes.append(payload[2 + i])
                length = lowlewel.multibyteval(lenbytes)
                length += 8  # 8 bytes of length value
            elif length > 125:
                return None  # unknown length

        except IndexError:
            return None

        length += 1  # first field
        length += 1  # basic payload field len
        length += 4  # mask len

        return length

    def get_payload_length(self, payload):
        try:
            length = payload[1] & 0x7F

            if length <= 125:
                return length
            if length == 126:  # length field is next two bytes
                lenbytes = []
                for i in range(0, 2):
                    lenbytes.append(payload[2 + i])
                length = lowlewel.multibyteval(lenbytes)
            elif length == 127:  # length field is next 8 bytes
                lenbytes = []
                for i in range(0, 8):
                    lenbytes.append(payload[2 + i])
                length = lowlewel.multibyteval(lenbytes)
            else:
                return None  # unknown length

        except IndexError:
            return None

        return length

    def unmask(self, payload):
        try:
            length = payload[1] & 0x7F
        except IndexError:
            return None

        if length <= 125:
            maskstart_index = 2
        elif length == 126:  # length field is next two bytes
            length = self.get_payload_length(payload)
            maskstart_index = 4
        elif length == 127:  # length field is next 8 bytes
            length = self.get_payload_length(payload)
            maskstart_index = 10
        else:
            return None  # unknown length

        if not length:
            return None

        try:  # if frame is not complete, return None
            maskkey = payload[maskstart_index:(maskstart_index + 5)]
            data = payload[(maskstart_index + 4):]
            data = data[:length]
        except IndexError:
            return None

        text = ''
        for i, c in enumerate(data):
            text += chr(c ^ maskkey[i % 4])

        return text

    def encode_data(self, data):
        byte1 = 0x80 | (0x01 & 0x0F)
        length = len(data)

        output_buffer = bytearray()
        output_buffer.append(byte1)

        if length <= 125:
            output_buffer.append(length)
        elif length <= 0xFFFF:
            output_buffer.append(126)
            lenbytes = lowlewel.multibytetoarray(length)
            for i in range(0, 2):
                try:
                    output_buffer.append(lenbytes[i])
                except IndexError:
                    output_buffer.append(0)
        else:
            output_buffer.append(127)
            lenbytes = lowlewel.multibytetoarray(length)
            for i in range(0, 8):
                try:
                    output_buffer.append(lenbytes[i])
                except IndexError:
                    output_buffer.append(0)
            return None

        for byte in data:
            output_buffer.append(byte)

        return output_buffer

    def data_from_websocket(self, data):
        print 'ws: ', data
        self.send('thank you')

    def send(self, data):
        output_buffer = self.encode_data(data)
        if not output_buffer:
            return
        try:
            self.socket.sendall(output_buffer)
        except:
            return

    def send_raw(self, data):
        try:
            self.socket.sendall(data)
        except:
            return

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
