import ConfigParser
import requests
import json

headers = {'Content-Type': 'application/json'}


class fileAdapter():
    def __init__(self, conf_path):
        config = ConfigParser.ConfigParser()
        config.read(conf_path)
        self.file_dir = config.get("file", "fileDir")

    def recv_from_url(self, url, remote_file_name, file_name):
        data = json.dumps({"file": str(remote_file_name)})
        with open(self.file_dir + file_name, 'wb') as handle:
            response = requests.post(url=url, headers=headers,
                                     data=data)

            if not response.ok:
                print "file reception failed"
                return

            for block in response.iter_content(1024):
                handle.write(block)
                continue
