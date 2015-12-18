from multiprocessing import Process
from time import sleep


class servo(object):
    def __init__(self, config, sID, blaster, lock, des_queue, cur_queue):
        self.cur_pos = 0
        self.blaster = blaster
        self.servo_str = "P1-" + config.get("servoConfig",
                                            "servo"+str(sID)+"Pin") + "="
        self.sID = sID

        volt_str = config.get("servoConfig", "servo"+str(sID) + "volt")
        volt_str = volt_str.split(",")
        self.servo_voltage = [int(volt_str[0]), int(volt_str[1])]
        self.ratio = float(self.servo_voltage[1] - self.servo_voltage[0])/180

        self.lock = lock
        self.sleepTime = 0.1

        self.des_queue = des_queue
        self.cur_queue = cur_queue

        # init
        lock.acquire()
        self.blaster.write(self.servo_str +
                           str(90 * self.ratio + self.servo_voltage[0]) + '\n')
        self.blaster.flush()
        lock.release()

        sleep(2)

        self.process = Process(target=self.move, args=())
        self.process.start()

    def move(self):
        cur_pos = 0
        while True:
            sleep(self.sleepTime)
            if (self.des_queue.empty()):
                pass
            else:
                des_pos = self.des_queue.get()

                if (des_pos == cur_pos or des_pos > 90 or des_pos < -90):
                    # posistion range [-90, 90]
                    pass
                else:
                    volt = float(des_pos + 90) * self.ratio + \
                        self.servo_voltage[0]
                    volt = max(self.servo_voltage[0], volt)
                    volt = min(self.servo_voltage[1], volt)
                    # print "voltage : " + str(volt)
                    self.lock.acquire()
                    self.blaster.write(self.servo_str + str(volt) + '\n')
                    self.blaster.flush()
                    self.lock.release()
                    cur_pos = des_pos
                    # print "servo" + str(self.sID) + " cur: " + str(cur_pos)
                    # print "servo" + str(self.sID) + " dst: " + str(des_pos)
                    self.cur_queue.put(cur_pos)

    def disable_servo(self):
        self.process.terminate()
