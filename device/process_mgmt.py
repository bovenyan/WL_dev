import psutil
from subprocess import Popen


def fetch_pids_of_port(ip, port):
    net_conn = psutil.net_connections()
    pids = []

    for conn in net_conn:
        if (ip in conn.raddr and port in conn.raddr):
            if (conn.pid is None):
                print "error: no pid detected"
            else:
                print "found PID: " + str(conn.pid)
                pids.append(conn.pid)
    return pids


def kill_pids_of_port(ip, port):
    for pid in fetch_pids_of_port(ip, port):
        print "pid: " + str(pid)
        Popen(["kill", "-9", str(pid)])

if __name__ == "__main__":
    kill_pids_of_port("192.168.1.4", 22)
