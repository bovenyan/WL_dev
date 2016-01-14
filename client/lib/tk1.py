from wikkit_device import WikkitDevice


class TK1(WikkitDevice):
    def __init__(self, url, dev_id):
        super(TK1, self).__init__(url, "tk1", dev_id)

    def route_query(self, query):
        if super(TK1, self).route_query(query):
            return True

        element = query.split()

        if (element[0] == "help"):  # print help
            self._print_help()
            return True

    def _print_help(self):
        print "Status: You are controlling tk1-" + str(self.dev_id)
        super(TK1, self)._print_help()
