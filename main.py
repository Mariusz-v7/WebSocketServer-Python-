import WebSocketServer.server


print "hello"

srv = WebSocketServer.server.Server(1234)
running = True

while running:
    command = raw_input('Enter command: ')
    if command == 'exit':
        running = False

print 'Closing the server...'
srv.close()