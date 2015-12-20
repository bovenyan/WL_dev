import psutil


def fetch_pid_of_port(port):
    net_conn = psutil.net_connections()
    pid = -1

    for conn in net_conn:
        if ('127.0.0.1' in conn.laddr and '10001' in conn.laddr):
            if (conn.pid is None):
                print "error: no pid detected"
            else:
                pid = conn.pid
            break
    return pid
