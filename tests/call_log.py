__author__ = 'ben'


class CallLog(object):

    fn_log = []

    @classmethod
    def reset(cls):
        del cls.fn_log[:]

    @classmethod
    def append(cls, value):
        cls.fn_log.append(value)

    @classmethod
    def get(cls):
        return cls.fn_log[:]
