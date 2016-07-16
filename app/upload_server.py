import socket


def init_socket():
    sock = socket.socket()
    host = socket.gethostname()
    port = 12346
    sock.bind((host, port))

    sock.listen(5)  # 5 means at most buffer 5 requests, drop overflowed req.
    return sock


def process_file_callback(content_str):
    # TODO: process file callback
    pass


# accept json requests and process
def start_service(sock):
    while True:
        try:
            c, addr = sock.accept()
            print 'Got connection from', addr
            # get file directory
            content_str = c.recv(100)

            # log
            delim = content_str.index(':')
            devId = int(content_str[: delim])
            print "Device ID: " + str(devId)
            print "Received file directory: "
            print content_str[delim + 1, :]

            c.close()
        except KeyboardInterrupt:
            # error handling
            break

        # process the received file
        process_file_callback(content_str)

if __name__ == "__main__":
    print "start service"
    sock = init_socket()
    start_service(sock)
    print "exiting... bye"
