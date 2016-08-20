import socket
import json


def init_socket():
    sock = socket.socket()
    host = socket.gethostname()
    port = 12347    # Do not modify
    sock.bind((host, port))

    sock.listen(5)  # 5 means at most buffer 5 requests, drop overflowed req.
    return sock


def process_file_callback(content_obj):
    # TODO: process file callback
    print str(content_obj)
    pass


# accept json requests and process
def start_service(sock):
    while True:
        try:
            print "Waiting... press Cntl+C to exit"
            c, addr = sock.accept()

            # receive content
            print 'Got connection from', addr
            content_str = c.recv(1000)  # 1000 is buffer size in bytes

            # parse device id
            delim = content_str.index("%")
            dev_id = content_str[:delim]
            print 'device ID ' + dev_id
            content_str = content_str[delim+1:]

            # retrieve device ID
            content_obj = json.loads(content_str)

            # process
            process_file_callback(content_obj)

            c.close()
        except KeyboardInterrupt:
            # error handling
            break

if __name__ == "__main__":
    print "start service"
    sock = init_socket()
    start_service(sock)
    print "exiting... bye"
