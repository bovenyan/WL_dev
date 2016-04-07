import MySQLdb
from datetime import datetime


class db_api(object):
    def __init__(self, config, dev_type):
        """
        parse configuration
        """
        self.hostip = config.get('dbconfig', 'hostip')
        self.user = config.get('dbconfig', 'dbuser')
        self.passwd = config.get('dbconfig', 'passwd')
        self.dbname = config.get('dbconfig', 'dbname')
        self.tablename = config.get('dbconfig', 'tablepref') + dev_type
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

    def disconnect(self):
        conn = self.conn()
        conn.close()

    # dev basic operation
    def update_activity(self, dev_id, usr_dev=True, conn=None, cur=None):
        try:
            to_shut = False
            if conn is None:
                conn = self.conn()
                cur = conn.cursor()
                to_shut = True

            if (usr_dev):
                cur.execute("update {} \
                            set last_operation=now() \
                            where id={}".format(self.tablename, dev_id))
            else:
                cur.execute("update {} \
                            set last_seen=now() \
                            where id={}".format(self.tablename, dev_id))
            conn.commit()

            if (to_shut):
                cur.close()
                conn.close()

            return True

        except Exception, e:
            print str(e)
            return False

    def get_mgmt_flag(self, dev_id, usr_dev=True):
        try:
            conn = self.conn()
            cur = conn.cursor()

            # fetch mgmt flags
            cur.execute("select manage_flags+0 from {} \
                        where id={}".format(self.tablename, dev_id))
            res = int(cur.fetchone()[0])

            self.update_activity(dev_id, usr_dev, conn, cur)

            cur.close()
            conn.close()
            return res

        except Exception, e:
            print str(e)
            return -1

    def set_mgmt_flag(self, dev_id, mgmt_flag, usr_dev=True):
        try:
            conn = self.conn()
            cur = conn.cursor()
            if (usr_dev):
                cur.execute("update {} \
                            set manage_flags={}, \
                            last_operation=now() \
                            where id={}".format(self.tablename, mgmt_flag,
                                                dev_id))
            else:
                cur.execute("update {} \
                            set manage_flags={}, \
                            last_seen=now() \
                            where id={}".format(self.tablename, mgmt_flag,
                                                dev_id))

            conn.commit()

            cur.close()
            conn.close()
            return True
        except Exception, e:
            print str(e)
            return False

    def get_op_codes(self, dev_id, usr_dev=True):
        try:
            conn = self.conn()
            cur = conn.cursor()

            cur.execute("select op_codes+0 from {} \
                        where id={}".format(self.tablename,
                                            dev_id))

            res = int(cur.fetchone()[0])

            self.update_activity(dev_id, usr_dev, conn, cur)

            cur.close()
            conn.close()

            return res
        except Exception, e:
            print str(e)
            return -1

    def set_op_codes(self, dev_id, op_codes, usr_dev=True):
        try:
            conn = self.conn()
            cur = conn.cursor()
            if (usr_dev):
                cur.execute("update {} \
                            set op_codes={}, \
                            last_operation=now() \
                            where id={}".format(self.tablename,
                                                op_codes,
                                                dev_id))
            else:
                cur.execute("update {} \
                            set op_codes={}, \
                            last_seen=now() \
                            where id={}".format(self.tablename,
                                                op_codes,
                                                dev_id))

            conn.commit()
            cur.close()
            return True
        except Exception, e:
            print str(e)
            return False

    def get_lastseen(self, dev_id):
        try:
            conn = self.conn()
            cur = conn.cursor()
            cur.execute("select last_seen from {} \
                        where id={}".format(self.tablename, dev_id))
            res = cur.fetchone()
            return res[0]
        except Exception, e:
            print str(e)
            return datetime.min

    def set_device(self, dev_id, mgmt_flags, op_codes, usr_dev=True):
        try:
            conn = self.conn()
            cur = conn.cursor()
            if (usr_dev):
                cur.execute("update {} \
                            set manage_flags={}, \
                            op_codes={}, \
                            last_operation=now() \
                            where id={}".format(self.tablename,
                                                mgmt_flags,
                                                op_codes,
                                                dev_id))
            else:
                cur.execute("update {} \
                            set manage_flags={}, \
                            op_codes={}, \
                            last_seen=now() \
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

    def disable_mgmt(self, dev_id, usr_dev=True):
        return self.set_device(dev_id, 4, 0, usr_dev)

    # device DB_APIs
    def device_get_mode(self, dev_id):
        """
        device read the mode_flags, mgmt_codes to control the device
        """
        try:
            conn = self.conn()
            cur = conn.cursor()
            """
            cur.execute("select last_operation, manage_flags+0, \
                        x_pos, y_pos, op_codes+0 from {} \
                        where id={}".format(self.tablename, dev_id))
            """
            cur.execute("select * from {} where id={}".format(self.tablename,
                                                              dev_id))
            res = cur.fetchone()

            self.update_activity(dev_id, conn, cur)

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
        return self.set_mgmt_flag(dev_id, 0, True)

    def device_reset_op(self, dev_id):
        """
        reset mgmt_codes
        """
        return self.set_op_codes(dev_id, 0, True)

    def device_set_busy(self, dev_id):
        mgmt_flag = self.get_mgmt_flag(dev_id, False)
        mgmt_flag = mgmt_flag | 8
        return self.set_mgmt_flag(dev_id, mgmt_flag, False)

    def device_reset_usr(self, dev_id):
        mgmt_flag = self.get_mgmt_flag(dev_id, False)

        if (not mgmt_flag & 4):  # no need to reset
            return True
        mgmt_flag = mgmt_flag & (~4)

        return self.set_mgmt_flag(dev_id, mgmt_flag, False)

    def device_flop_mgmt(self, dev_id, tofetch):
        """
        reset the apply flag, and set the fetch flag if necessary
        """
        mgmt_flag = self.get_mgmt_flag & (~4)
        if (tofetch):
            mgmt_flag = mgmt_flag | 8

        return self.set_mgmt_flag(dev_id, mgmt_flag)

    # API for ursers
    def usr_enable_mgmt(self, dev_id, usr_dev=True):
        if (self.usr_check_dev_mgmt(dev_id)):  # already mgmt
            return [True, True]
        else:
            return [self.set_device(dev_id, 5, 0, usr_dev),  # need wait
                    False]

    def usr_check_dev_mgmt(self, dev_id):
        manage_f = self.get_mgmt_flag(dev_id)
        op_codes = self.get_op_codes(dev_id)
        return (bool(manage_f & 1) and   # mgmt must be 1 & mgmt must be applied
                (op_codes != 0 or (not bool(manage_f & 4))))

    def usr_check_dev_ready(self, dev_id):
        manage_f = self.get_mgmt_flag(dev_id)
        print manage_f
        if (not (manage_f & 4) and (manage_f & 8)):
            return True
        return False

    def usr_ssh_enable(self, dev_id):
        print "enabled ssh"
        return self.set_device(dev_id, 5, 32)

    def usr_ssh_disable(self, dev_id):
        return self.set_device(dev_id, 5, 64)

    def usr_ssh_restart(self, dev_id):
        return self.set_device(dev_id, 5, 96)

    def usr_reset(self, dev_id):
        return self.set_mgmt_flag(dev_id, 16)


if __name__ == "__main__":
    cc = db_api('./config.ini')
    cc.device_reset_op(1)
    print cc.device_get_rec(2)
