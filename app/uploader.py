import requests
from subprocess import call
import os
import time

headers = {'Content-Type': 'application/json'}


def request_start(url, devId):
    data = {
        "devId": devId
    }

    response = requests.post(url, data=data, headers=headers)

    if (response.ok and not (response.json() is None)):
        return response.json()

    return None


def send_signal(url, signal_code, devId):
    """
    start: signal_code = 0
    end: signal_code = 1
    abort: signal_code = 2
    """
    if signal_code == 0:
        send_success = False
        while (not send_success):
            try:
                response = requests.get(url + "/")
                if (response.ok):
                    send_success = True
            except Exception, e:
                print "error signal code: " + str(e)


def split_file(file_path, chunk_path, token, split_len):
    call(["mkdir", "-p", chunk_path])
    call(["rm", "-r", chunk_path+"/*"])
    call(["split", file_path, "--bytes="+split_len+"M", "/tmp/parts"+token])

    # call(["cat", token+"*", ">", token])


def send_chunks(url, token, chunk_path):
    # TODO: put this into a thread which can listen to a kill event
    idx = 0
    for subdir, dirs, files in os.walk("/tmp/parts"):
        while idx < len(files):
            files = {'file': open(files[idx], 'rb')}
            try:
                response = requests.post(url, files=files)
                if not response.ok:
                    print "failed to send file chunk" + str(idx)
                    + ", retransmit"
                else:
                    ++idx
            except Exception, e:
                print "error happens for file: " + str(e)


def confirm_end(url, token):
    confirmed = False
    while (not confirmed):
        try:
            response = requests.post(url, data=token)
            if (response.ok):
                confirmed = True
        except Exception, e:
            print "error sending confirm message: " + str(e)
            confirmed = False


def killer(send_thread_fd, sleep_time):
    time.sleep(sleep_time)
    # TODO: thread.kill(send_thread_fd)

if __name__ == "__main__":
    # FIXME configuration
    chunk_path = "/tmp/parts"
    file_path = "./test.img"
    url = "127.0.0.1:5000"
    # chunk_size = 1024*1024   # 1M at a time
    chunk_size = 1024   # 1K at a time
    token = ""
    # TODO: token = random_string_gen()

    request_start(url + "/upload/test")
    # TODO: record time an register a listen thread
    split_file(url)
    send_chunks(url, token, chunk_path)
