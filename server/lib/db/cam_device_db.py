from wikkit_device_db import db_api


class cam_db_api(db_api):
    def __init__(self, config):
        super(cam_db_api, self).__init__(config, "piCam")

    def device_get_mode(self, dev_id):
        res = {}
        try:
            conn = self.conn()
            cur = conn.cursor()

            cur.execute("select last_operation, last_seen, manage_flags+0, \
                        op_codes+0, x_pos, y_pos from {} \
                        where id={}".format(self.tablename, dev_id))
            res_array = cur.fetchone()

            res["last_operation"] = res_array[0]
            res["last_seen"] = res_array[1]
            res["manage_flags"] = int(res_array[2])
            res["op_codes"] = int(res_array[3])
            res["pos_x"] = int(res_array[4])
            res["pos_y"] = int(res_array[5])

        except Exception, e:
            print str(e)

        return res

    def device_update_pos(self, dev_id, pos_x, pos_y):
        """
        update the position of the servo
        """
        if (pos_x > 90 or pos_x < -90 or pos_y > 90, pos_y < -90):
            return False
        try:
            conn = self.conn()
            cur = conn.cursor()
            cur.execute("update {} \
                        set x_pos={}, \
                        y_pos={}, \
                        last_seen=now()\
                        where id={}".format(self.tablename, pos_x,
                                            pos_y, dev_id))
            conn.commit()
            cur.close()
            return True
        except Exception, e:
            print str(e)
            return False

    def usr_servo_inc(self, dev_id, inc_dec, xy):
        self.set_mgmt_flag(dev_id, 5)

        op_codes = 1
        if (not xy):  # horizontal
            op_codes = op_codes + inc_dec * 4
        else:
            op_codes = op_codes + inc_dec * 8

        return self.set_op_codes(op_codes, dev_id)

    def usr_servo_pos(self, dev_id, pos_x, pos_y):
        try:
            conn = self.conn()
            cur = conn.cursor()
            cur.execute("update {} \
                        set manage_flags=5, \
                        op_codes=3, \
                        x_pos={}, y_pos={} \
                        where id ={}".format(self.tablename, pos_x,
                                             pos_y, dev_id))
            conn.commit()
            cur.close()
            return True
        except Exception, e:
            print str(e)
            return False

    def usr_servo_sav(self, dev_id):
        return self.set_op_codes(128, dev_id)

    def usr_take_pic(self, dev_id):
        return self.set_device(dev_id, 5, 16)

    """
    def user_fetch_avail(self, dev_id):
        mgmt_flag = self.get_mgmt_flag(dev_id)
        return bool(mgmt_flag & 8)
    """
