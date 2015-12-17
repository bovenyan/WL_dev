import MySQLdb
# import os
import ConfigParser


class db_api(object):
    def __init__(self, conf_path):
        """
        parse configuration
        """
        config = ConfigParser.ConfigParser()
        config.read(conf_path)
        self.hostip = config.get('dbconfig', 'hostip')
        self.user = config.get('dbconfig', 'dbuser')
        self.passwd = config.get('dbconfig', 'passwd')
        self.dbname = config.get('dbconfig', 'dbname')
        self.tablename = config.get('dbconfig', 'tablename')
        self.port = config.get('dbconfig', 'port')
        self.charset = config.get('dbconfig', 'charset')

    def conn(self):
        """
        connecting to the database
        """
        try:
            conn = MySQLdb.connect(host=self.hostip, user=self.user,
                                   passwd=self.passwd, db=self.dbname,
                                   port=int(self.port), charset=self.charset)
            conn.ping(True)
            return conn
        except MySQLdb.Error, e:
            error_msg = 'Error {}: {}'.format(e.args[0], e.args[1])
            print error_msg

    def get_host_version(self):
        conn = self.conn()
        try:
            cus = conn.cursor()
            cus.execute("SELECT VERSION()")
            row = cus.fetchone()
            if row is not None:
                return row[0]
            else:
                return 'fail to connect '
        except MySQLdb.Error, e:
            cus.rollback()
            error_msg = 'Error %d: %s' % (e.args[0], e.args[1])
            print error_msg
            # Log.Error_Log(error_msg)

    def disconnect(self):
        conn = self.conn()
        conn.close()

    # dev basic operation
    def user_enter_mgmt(self, dev_id):
        try:
            conn = self.conn()
            cur = conn.cursor()
            cur.execute("update {} \
                        set manage_flags=1, \
                        op_codes=0 \
                        where id={}".format(self.tablename, dev_id))
            conn.commit()
            cur.close()
            return True
        except Exception, e:
            print str(e)
            return False

    def user_close_mgmt(self, dev_id):
        return self.device_reset_op(dev_id)

    def get_mgmt_flag(self, dev_id):
        try:
            conn = self.conn()
            cur = conn.cursor()
            cur.execute("select manage_flags+0 from {} \
                        where id={}".format(self.tablename, dev_id))
            return int(cur.fetchone())
        except Exception, e:
            print str(e)
            return -1

    def set_mgmt_flag(self, dev_id, mgmt_flag):
        try:
            conn = self.conn()
            cur = conn.cursor()
            cur.execute("update {} \
                        set manage_flags={}, \
                        where id={}".format(self.tablename, mgmt_flag,
                                            dev_id))
            conn.commit()
            cur.close()
            return True
        except Exception, e:
            print str(e)
            return False

    def get_op_codes(self, dev_id):
        try:
            conn = self.conn()
            cur = conn.cursor()
            cur.execute("select op_codes+0 from {} \
                        where id={}".format(self.tablename,
                                            dev_id))
            return int(cur.fetchone())
        except Exception, e:
            print str(e)
            return -1

    def set_op_codes(self, dev_id, op_codes):
        try:
            conn = self.conn()
            cur = conn.cursor()
            cur.execute("update {} \
                        set op_codes={}, \
                        where id={}".format(self.tablename,
                                            op_codes,
                                            dev_id))
            conn.commit()
            cur.close()
            return True
        except Exception, e:
            print str(e)
            return False

    def set_device(self, dev_id, mgmt_flags, op_codes):
        try:
            conn = self.conn()
            cur = conn.cursor()
            cur.execute("update {} \
                        set manage_flags={}, \
                        op_codes={}, \
                        where id={}".format(self.tablename,
                                            mgmt_flags,
                                            op_codes,
                                            dev_id))
            conn.commit()
            cur.close()
            return True
        except Exception, e:
            print str(e)
            return False

    # device DB_APIs
    def device_get_rec(self, dev_id):
        """
        device read the mode_flags, mgmt_codes to control the device
        """
        try:
            conn = self.conn()
            cur = conn.cursor()
            cur.execute("select id, last_operation, manage_flags+0, \
                        x_pos, y_pos, op_codes+0 from {} \
                        where id={}".format(self.tablename, dev_id))
            res = cur.fetchone()

            #  TODO: update heart beat timestamp
            cur.execute("update {} \
                     set last_seen=now() \
                     where id={}".format(self.tablename, dev_id))
            conn.commit()
            cur.close()
            return res
        except Exception, e:
            print str(e)
            return None

    def device_reset_mgmt(self, dev_id):
        """
        reset the mode flags
        """
        return self.set_mgmt_flag(dev_id, 0)

    def device_reset_op(self, dev_id):
        """
        reset mgmt_codes
        """
        return self.set_op_codes(dev_id, 0)

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
                        y_pos={} \
                        where id={}".format(self.tablename, pos_x,
                                            pos_y, dev_id))
            conn.commit()
            cur.close()
            return True
        except Exception, e:
            print str(e)
            return False

    def device_flop_mgmt(self, dev_id, tofetch):
        """
        reset the apply flag, and set the fetch flag if necessary
        """
        mgmt_flag = self.get_mgmt_flag & (~4)
        if (tofetch):
            mgmt_flag = mgmt_flag | 8

        return self.set_mgmt_flag(devId, mgmt_flag)

    # API for ursers

    def user_check_dev_mgmt(self, dev_id):
        manage_f = get_mgmt_flag(dev_id)
        return bool(manage_f & 1)

    def user_check_dev_avail(self, dev_id):
        manage_f = get_mgmt_flag(dev_id)
        if (not (manage_f & 4) and not (manage_f & 8)):
            return True
        return False

    def user_servo_inc(self, dev_id, inc_dec, xy):
        self.set_mgmt_flag(dev_id, 5)

        op_codes = 1
        if (not xy):  # horizontal
            op_codes = op_codes + inc_dec * 4
        else:
            op_codes = op_codes + inc_dec * 8

        return self.set_op_codes(op_codes, dev_id)

    def user_servo_pos(self, dev_id, pos_x, pos_y):
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

    def user_ssh_enable(self, dev_id):
        return set_device(dev_id, 5, 32)

    def user_reset(self, dev_id):
        return self.set_mgmt_flag(dev_id, 16)

    def user_take_pic(self, dev_id):
        return set_device(dev_id, 5, 16)

    def user_fetch_avail(self, dev_id):
        mgmt_flag = get_mgmt_flag(dev_id)
        return (mgmt_flag & 8)


if __name__ == "__main__":
    cc = db_api('./config.ini')
    cc.device_reset_op(1)
    # cc.device_update_pos(1, 50, 50)
    # cc.device_flop_mgmt(1, 1)

    print cc.device_get_rec(2)
