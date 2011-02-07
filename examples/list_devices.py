
from pylibftdi import Driver

for device in Driver().list_devices():
    print("%s:%s:%s"%(tuple(x.decode('latin1') for x in device)))
