from wikkit_device_db import db_api


class tk1_db_api(db_api):
    def __init__(self, conf_path):
        super(tk1_db_api, self).__init__(conf_path, "tk1")

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

        except Exception, e:
            print str(e)

        return res
