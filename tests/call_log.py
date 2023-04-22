__author__ = "ben"


class CallLog:
    fn_log: list[str] = []

    @classmethod
    def reset(cls):
        cls.fn_log.clear()

    @classmethod
    def append(cls, value):
        cls.fn_log.append(value)

    @classmethod
    def get(cls):
        return cls.fn_log.copy()
