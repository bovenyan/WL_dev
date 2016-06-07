import requests
from subprocess import call
from multiprocessing import Process
import os
from time import sleep
import hashlib


# TODO: the following parts should be imported as header

headers = {'Content-Type': 'application/json'}


def request_start(url, devId):
    url = url + str(devId) + "/req_start"
    response = requests.get(url, headers=headers)

    if (response.ok and not (response.json() is None)):
        res = response.json()
        return res["token"]

    return None


def split_file(file_path, chunk_path, token, split_len):
    call(["mkdir", "-p", chunk_path])
    call(["rm", "-r", chunk_path+"/*"])
    call(["split", file_path, "--bytes="+split_len+"M", chunk_path+"/"+token])
    # call(["cat", token+"*", ">", token])


def send_chunks(url, devId, chunk_path, success_backoff, failure_backoff):
    url = url + str(devId) + "/send_chunks"

    idx = 0

    for subdir, dirs, files in os.walk("/tmp/parts"):
        while idx < len(files):
            digester = hashlib.md5()
            with open(files[idx], "rb") as f:
                for piece in iter(lambda: f.read(4096), b""):
                    digester.update(piece)
            chksum = digester.hexdigest()

            files = {'file': open(files[idx], 'rb')}
            try:
                response = requests.post(url, files=files,
                                         data={"chksum": chksum})
                if not response.ok:
                    print "chunk " + str(files[idx].name) + \
                        " failed, retransmit..."
                    sleep(failure_backoff)
                elif "fail_code" in response.json():
                    print "chunk " + str(files[idx].name) + \
                        " corrupted, retransmit..."
                    sleep(failure_backoff)
                else:
                    print "chunk " + str(idx) + " received!"
                    ++idx
                    sleep(success_backoff)
            except Exception, e:
                print "error happens for file: " + str(e)
                sleep(failure_backoff)


if __name__ == "__main__":
    # TODO: the following parameters should be put into config file
    devId = 1
    kill_timeout = 1800  # if uploading is not completed in kill_to sec, kill it
    url = "127.0.0.1:5000/night/"

    chunk_path = "/tmp/parts"
    file_path = "./test.img"
    # chunk_size = 1024*1024   # 1M at a time
    chunk_size = 1024   # 1K at a time

    success_backoff = 5
    failure_backoff = 30

    # TODO: the following piece of program should be integrated in program
    split_file(url)

    token = None

    while token is None:
        token = request_start(url, devId)
        if token is None:
            sleep(failure_backoff)

    proc = Process(target=send_chunks, args=(url, devId, chunk_path,
                                             success_backoff,
                                             failure_backoff))
    proc.start()

    sleep(kill_timeout)

    if (proc.is_alive()):
        print "Upload failed to accomplish in " + str(kill_timeout) + " sec"
        print "Maybe network is too slow.. Killed.."
        proc.terminate()

    send_chunks(url, chunk_path)
