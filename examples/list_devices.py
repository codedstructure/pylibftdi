

from pylibftdi import Driver


for device in Driver().list_devices():
    print("%s:%s:%s"%(device))
