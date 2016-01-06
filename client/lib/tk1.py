from wikkit_device import WikkitDevice


class TK1(WikkitDevice):
    def __init__(self, url, dev_id):
        self.dev_type = 1
        self.url = url + "tk1/"
        self.dev_id = dev_id
        self.name = "TK1-" + str(dev_id)

        super(TK1, self).__init__(self.url, dev_id, 0)

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
