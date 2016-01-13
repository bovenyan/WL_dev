import psutil
from subprocess import Popen


def fetch_pids_of_port(port):
    net_conn = psutil.net_connections()
    pids = []

    for conn in net_conn:
        if ('127.0.0.1' in conn.laddr and port in conn.laddr):
            if (conn.pid is None):
                print "error: no pid detected"
            else:
                print "found PID: " + str(conn.pid)
                pids.append(conn.pid)
    return pids


def kill_pids_of_port(port):
    for pid in fetch_pids_of_port(port):
        print "pid: " + str(pid)
        Popen(["kill", "-9", str(pid)])
