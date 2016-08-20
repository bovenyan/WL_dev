import requests
import json


headers = {'Content-Type': 'application/json'}
url = "http://120.76.26.101:8000/tk1/return_customer/h_count"
dev_id = 1
url_full = url + "/" + str(dev_id)


def post_headcount_trace(trace):
    data = json.dumps(trace)
    try:
        requests.post(url_full, data=data, headers=headers)
    except Exception, e:
        print "error posting trace" + str(e)

if __name__ == "__main__":
    trace = [{"IsTopView": "True"},
             {"direction": 1,
              "LifeEnd": 1471211826.667518,
              "LifeStart": 1471211826},
             {"direction": -1,
              "LifeEnd": 1471211833.067796,
              "LifeStart": 1471211833},
             {"direction": -1,
              "LifeEnd": 1471211839.770326,
              "LifeStart": 1471211839}]

    post_headcount_trace(trace)
