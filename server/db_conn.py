import MySQLdb
# import os
import ConfigParser


class db_api(object):
    def __init__(self, conf_path):
        config = ConfigParser.ConfigParser()
        config.read(conf_path)
        self.hostip = config.get('dbconfig', 'hostip')
        self.user = config.get('dbconfig', 'dbuser')
        self.passwd = config.get('dbconfig', 'passwd')
        self.dbname = config.get('dbconfig', 'dbname')
        self.port = config.get('dbconfig', 'port')
        self.charset = config.get('dbconfig', 'charset')

    def conn(self):
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

    def insert_sql_cmd(self, sql_cmd):
        try:
            conn = self.conn()
            cur = conn.cursor()
            cur.execute(sql_cmd)
            conn.commit()
            cur.close()
            return True
        except Exception, e:
            print "[MYSQL ERROR] : {}".format(sql_cmd)
            print str(e)
            cur.close()
            return False

    def update_sql_cmd(self, sql_cmd):
        try:
            conn = self.conn()
            cur = conn.cursor()
            cur.execute(sql_cmd)
            conn.commit()
            cur.close()
            return True
        except Exception, e:
            print "[MYSQL ERROR] : {}".format(sql_cmd)
            print str(e)
            cur.close()
            return False

    def query_sql_cmd(self, sql_cmd):
        try:
            conn = self.conn()
            cur = conn.cursor()
            cur.execute(sql_cmd)
            res = cur.fetchall()
            cur.close()
            return res
        except Exception, e:
            print "[MYSQL ERROR] : {}".format(sql_cmd)
            print str(e)
            return False

    # device DB_APIs
    def device_get_rec(self, dev_id):
        try:
            conn = self.conn()
            cur = conn.cursor()
            cur.execute("select id, last_operation, manage_flags+0, \
                        x_pos, y_pos, op_codes+0 from device \
                        where id={}".format(dev_id))
            res = cur.fetchone()

            #  TODO: update heart beat timestamp
            cur.execute("update device \
                     set last_seen=now() \
                     where id={}".format(dev_id))
            conn.commit()
            cur.close()
            return res
        except Exception, e:
            print str(e)
            return None

    def device_reset(self, dev_id):
	return self.device_reset_mgmt(dev_id) & self.device_reset_op(dev_id)

    def device_reset_mgmt(self, dev_id):
        try:
            conn = self.conn()
            cur = conn.cursor()
            cur.execute("update device \
                        set manage_flags=0 \
                        where id={}".format(dev_id))
            conn.commit()
            cur.close()
            return True
        except Exception, e:
            print str(e)
            return False

    def device_reset_op(self, dev_id):
        try:
            conn = self.conn()
            cur = conn.cursor()
            cur.execute("update device \
                        set op_codes=0 \
                        where id={}".format(dev_id))
            conn.commit()
            cur.close()
            return True
        except Exception, e:
            print str(e)
            return False

    def device_update_pos(self, dev_id, pos_x, pos_y):
        if (pos_x > 90 or pos_x < -90 or pos_y > 90, pos_y < -90):
            return False
        try:
            conn = self.conn()
            cur = conn.cursor()
            cur.execute("update device \
                        set x_pos={}, \
                        y_pos={} \
                        where id={}".format(pos_x, pos_y, dev_id))
            conn.commit()
            cur.close()
            return True
        except Exception, e:
            print str(e)
            return False

    def device_flop_mgmt(self, dev_id, tofetch):
        try:
            conn = self.conn()
            cur = conn.cursor()
            cur.execute("update device \
                        set manage_flags=manage_flags & 11 \
                        where id={}".format(dev_id))
            if tofetch != 0:
                cur.execute("update device \
                            set manage_flags=manage_flags | 8 \
                            where id={}".format(dev_id))
            conn.commit()
            cur.close()
            return True
        except Exception, e:
            print str(e)
            return False

    # API for ursers
    def user_enter_mgmt(self, dev_id):
        try:
            conn = self.conn()
            cur = conn.cursor()
            cur.execute("update device \
                        set manage_flags=1, \
                        op_codes=0 \
                        where id={}".format(dev_id))
            conn.commit()
            cur.close()
            return True
        except Exception, e:
            print str(e)
            return False

    def user_close_mgmt(self, dev_id):
        return self.device_reset_op(dev_id)

    def user_check_dev_avail(self, dev_id):
        try:
            conn = self.conn()
            cur = conn.cursor()
            cur.execute("select manage_flags+0 from device \
                        where id={}".format(dev_id))
            manage_f = int(cur.fetchone())
            if (not (manage_f & 4) and not (manage_f & 8)):
                return True
            return False
        except Exception, e:
            print str(e)
            return False

    def user_servo_inc(self, dev_id, inc_dec, xy):
        try:
            conn = self.conn()
            cur = conn.cursor()

            op_codes = 1

            if (not xy):  # horizontal
                op_codes = op_codes + inc_dec * 4
            else:
                op_codes = op_codes + inc_dec * 8

            cur.execute("update device \
                        set manage_flags=5, \
                        op_codes={} \
                        where id={}".format(op_codes, dev_id))

            conn.commit()
            cur.close()
            return True
        except Exception, e:
            print str(e)
            return False

    def user_servo_pos(self, dev_id, pos_x, pos_y):
        try:
            conn = self.conn()
            cur = conn.cursor()
            cur.execute("update device \
                        set manage_flags=5, \
                        op_codes=3, \
                        x_pos={}, y_pos={} \
                        where id ={}".format(pos_x, pos_y, dev_id))
            conn.commit()
            cur.close()
            return True
        except Exception, e:
            print str(e)
            return False

    def user_ssh_enable(self, dev_id):
        try:
            conn = self.conn()
            cur = conn.cursor()
            cur.execute("update device \
                        set manage_flags=5, \
                        op_codes=32 \
                        where id ={}".format(dev_id))
            conn.commit()
            cur.close()
            return True
        except Exception, e:
            print str(e)
            return False

    def user_take_pic(self, dev_id):
        try:
            conn = self.conn()
            cur = conn.cursor()
            cur.execute("update device \
                        set manage_flags=5, \
                        op_codes=16 \
                        where id ={}".format(dev_id))
            conn.commit()
            cur.close()
            return True
        except Exception, e:
            print str(e)
            return False

    def user_fetch_avail(self, dev_id):
        try:
            conn = self.conn()
            cur = conn.cursor()
            cur.execute("select manage_flags+0 from device \
                        where id={}".format(dev_id))
            manage_f = int(cur.fetchone())

            if (manage_f & 8):
                return True
            return False
        except Exception, e:
            print str(e)
            return False


if __name__ == "__main__":
    cc = db_api('./config.ini')
    cc.device_reset_op(1)
    # cc.device_update_pos(1, 50, 50)
    # cc.device_flop_mgmt(1, 1)

    print cc.device_get_rec(2)
