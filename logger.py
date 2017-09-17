import logging
import logging.handlers


class Logger:

    write = None

    def __init__(self):
        syslog = logging.handlers.SysLogHandler(address='/dev/log')
        syslog.setFormatter(logging.Formatter('%(filename)s::%(funcName)s[%(process)d]: %(levelname)s %(message)s'))
        Logger.write = logging.getLogger()
        Logger.write.addHandler(syslog)
        Logger.write.setLevel(logging.DEBUG)

    def __call__(self):
        return Logger.write