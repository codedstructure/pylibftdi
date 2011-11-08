
from pylibftdi import Driver


def get_devices():
    dev_list = []
    for device in Driver().list_devices():
        dev_list.append("%s:%s:%s" % (tuple(x.decode('latin1') for x in device)))


if __name__ == '__main__':
    print('\n'.join(get_devices()))
