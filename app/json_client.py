import socket
import json

# TODO: load the website and put the call_back in

host = socket.gethostname()
port = 12345


def call_back_in_web(json_obj):
    sock = socket.socket()

    sock.connect((host, port))

    print "Sending content:"
    sock.send(json.dumps(json_obj, sort_keys=True))

    feed_back = sock.recv(256)
    print feed_back

    sock.close()

if __name__ == "__main__":
    obj = {}
    obj[0] = "friendship's little boat"
    obj[1] = "say sink..."

    call_back_in_web(obj)
