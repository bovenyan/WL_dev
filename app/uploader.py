import requests
from subprocess import Popen
from multiprocessing import Process
import os
from time import sleep
import hashlib
import json


# TODO: the following parts should be imported as header

headers = {'Content-Type': 'application/json'}


def request_start(url, devId):
    url = url + str(devId) + "/req_start"
    try:
        response = requests.get(url, headers=headers)
        if (response.ok and not (response.json() is None) and
           "filename" in response.json()):
            res = response.json()
            return res["filename"]

    except Exception, e:
        print "error requesting start " + str(e)
        return None

    return None


def inform_kill(url, devId):
    url = url + str(devId) + "/info_kill"

    try:
        requests.post(url)
    except Exception, e:
        print "error informing kill " + str(e)


def split_file(file_path, chunk_path, filename, split_len):
    Popen(["mkdir", "-p", chunk_path])
    proc_rm = Popen(['rm -r ' + chunk_path +'/*'], shell=True)
    proc_rm.wait()
    proc_split = Popen(["split", file_path,
          "--bytes="+str(split_len)+"M", chunk_path+"/"+filename])
    proc_split.wait()


def cal_chksum(file_name):
    digester = hashlib.md5()
    with open(file_name, "rb") as f:
        for piece in iter(lambda: f.read(4096), b""):
            digester.update(piece)
    return digester.hexdigest()


def confirm_done(url, devId, filename):
    url_confirm = url + str(devId) + "/confirm_done"

    data = json.dumps({"filename": filename})
    try:
        requests.post(url_confirm, data=data,
                      headers=headers)
    except Exception, e:
        print "error confirming " + str(e)


def send_chunks(url, devId, chunk_path, filename,
                success_backoff, failure_backoff):
    url_send = url + str(devId) + "/send_chunk"

    idx = 0

    for subdir, dirs, files in os.walk(chunk_path):
        while idx < len(files):
            file_dir = chunk_path +'/' + files[idx]
            print file_dir
            to_send_file = {'file': open(file_dir, 'rb')}
            try:
                chksum = cal_chksum(file_dir)
                response = requests.post(url_send, files=to_send_file,
                                         data={"chksum": chksum,
                                               "chunkname": files[idx]})
                if not response.ok:
                    print "chunk " + str(files[idx]) + \
                        " failed, retransmit..."
                    sleep(failure_backoff)
                elif "fail_code" in response.json():
                    print "chunk " + str(files[idx]) + \
                        " corrupted, retransmit..."
                    sleep(failure_backoff)
                else:
                    print "chunk " + str(idx) + " received!"
                    idx = idx+1
                    sleep(success_backoff)
            except Exception, e:
                print "error happens for file: " + str(e)
                sleep(failure_backoff)
    confirm_done(url, devId, filename)


if __name__ == "__main__":
    # TODO: the following parameters should be put into config file
    devId = 1
    kill_timeout = 1800  # if uploading is not completed in kill_to sec, kill it
    url = "http://172.31.1.2:5000/night/"

    chunk_path = "/tmp/parts"
    file_path = "./test.img"
    chunk_size = 1   # 1M at a time

    success_backoff = 5
    failure_backoff = 30

    # TODO: the following piece of program should be integrated in program

    filename = None

    while filename is None:
        filename = request_start(url, devId)
        print "received token: " + filename
        if filename is None:
            print "wait"
            sleep(failure_backoff)
        else:
            print "splitting ...."
            split_file(file_path, chunk_path, filename, chunk_size)
            break;

    proc = Process(target=send_chunks, args=(url, devId, chunk_path,
                                             filename,
                                             success_backoff,
                                             failure_backoff))
    proc.start()

    sleep(kill_timeout)

    if (proc.is_alive()):
        print "Upload failed to accomplish in " + str(kill_timeout) + " sec"
        print "Maybe network is too slow.. Killed.."
        proc.terminate()
        inform_kill(url, devId)
