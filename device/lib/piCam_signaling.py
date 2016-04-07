from lib.wikkit_signaling import wikkit_signaling
from multiprocessing import Lock, Queue
from servo import servo
import os
from time import sleep


class cam_signaling(wikkit_signaling):
    def __init__(self, config):
        super(cam_signaling, self).__init__(config)

        self.blaster = open('/dev/servoblaster', 'w')

        self.des_queue_x = Queue()
        self.des_queue_y = Queue()
        self.cur_queue_x = Queue()
        self.cur_queue_y = Queue()

        lock = Lock()
        self.servo_x = None
        self.servo_y = None

        self.step = int(config.get("servoConfig", "step"))

        self.servo_x = servo(config, 0, self.blaster, lock,
                             self.des_queue_x, self.cur_queue_x)
        self.servo_y = servo(config, 1, self.blaster, lock,
                             self.des_queue_y, self.cur_queue_y)
        self.servo_positions = [0, 0]

    def _handle_reset(self):
        super(cam_signaling, self)._handle_reset()
        self.des_queue_x.put(0)
        self.cur_queue_x.put(0)

    def _handle_mgmt(self, reply, options):
        response = super(cam_signaling, self)._handle_mgmt(reply, options)

        if ("type" in options and options["type"] == "servo" and
           self.dev_type == "piCam"):
            servo_turn_mode = 0
            servo_inc_xy = 0
            pos_x = 0
            pos_y = 0

            try:
                servo_turn_mode = int(options["servo_turn_mode"])
                servo_inc_xy = int(options["servo_inc_xy"])
                pos_x = int(options["pos_x"])
                pos_y = int(options["pos_y"])

                if (not servo_turn_mode):
                    if (not servo_inc_xy):
                        self.des_queue_x.put(self.servo_positions[0] +
                                             self.step)
                    else:
                        self.des_queue_x.put(self.servo_positions[1] +
                                             self.step)
                else:
                    self.des_queue_x.put(pos_x)
                    self.des_queue_y.put(pos_y)

                sleep(1)

                if (not self.cur_queue_x.empty()):
                    self.servo_positions[0] = self.cur_queue_x.get()
                if (not self.cur_queue_y.empty()):
                    self.servo_positions[1] = self.cur_queue_y.get()

                if (self.servo_positions[0] == pos_x and
                   self.servo_positions[1] == pos_y):
                    response["servo"] = True
                    response["pos_x"] = self.servo_positions[0]
                    response["pos_y"] = self.servo_positions[1]
                else:
                    response["servo"] = False

            except Exception, e:
                global logging
                logging.error(str(e))
                logging.warning("invalid servo input")

        if ("type" in options and options["type"] == "picture" and
           self.dev_type == "piCam"):
            print "I'm taking picture"
            filename = str(self.dev_type) + "-" + \
                str(self.dev_id) + ".jpg"
            os.popen("rm " + filename)
            os.popen("raspistill -w 640 -h 480 -t 1 -q 50 -o  " + \
                     filename + " &")
            sleep(1)  # wait for picture to take
            response["picture"] = True

        return response

    def distroy_channel(self):
        self.servo_x.disable_servo()
        self.servo_y.disable_servo()
