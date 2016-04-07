from lib.piCam_signaling import cam_signaling
from lib.tk1_signaling import tk1_signaling
import ConfigParser
import signal

config = ConfigParser.ConfigParser()
config.read("/opt/wikkit/signal/config.ini")
dev_type = config.get("signalConfig", "devType")

if dev_type == "piCam":
    device = cam_signaling(config)
    signal.signal(signal.SIGTERM, device.distroy_channel)
    signal.signal(signal.SIGINT, device.distroy_channel)
    device.run()

if dev_type == "tk1":
    device = tk1_signaling(config)
    device.run()
