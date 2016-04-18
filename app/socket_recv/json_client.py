import socket
import json

sock = socket.socket()
host = socket.gethostname()
port = 12345
sock.bind((host, port))

sock.listen(5)

while True:
    c, addr = sock.accept()
    print 'Got connection from', addr
    # FIXME: is 1024 enough ???
    content_str = c.recv(1024)
    obj = json.loads(content_str)
    print obj

    c.close()
