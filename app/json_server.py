import socket
import json


def init_socket():
    sock = socket.socket()
    host = socket.gethostname()
    port = 12345
    sock.bind((host, port))

    sock.listen(5)  # 5 means at most buffer 5 requests, drop overflowed req.
    return sock


def load_model():
    # TODO: load the model
    pass


# accept json requests and process
def start_service(sock):
    while True:
        try:
            c, addr = sock.accept()
            print 'Got connection from', addr
            # FIXME: is 1024 enough ???
            content_str = c.recv(1024)
            obj = json.loads(content_str)

            # TODO: use the model to process the requests
            print "Received json: "
            print obj[u'0']
            print obj[u'1']

            # TODO: return the results
            c.send("Go sink!!")
            c.close()
        except KeyboardInterrupt:
            break

if __name__ == "__main__":
    print "start service"
    load_model()
    sock = init_socket()
    start_service(sock)
    print "exiting... bye"
