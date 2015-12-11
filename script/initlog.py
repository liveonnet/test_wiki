#coding=utf8

import os
import sys
import logging
import logging.handlers
reload(sys)
sys.setdefaultencoding('utf8')

_LOCAL_PATH_ = os.path.abspath(os.path.dirname(__file__))
#-#for _path in (os.path.abspath(_LOCAL_PATH_ + '/../..'), os.path.abspath(_LOCAL_PATH_ + '/../../lib'), os.path.abspath(_LOCAL_PATH_ + '/../../applib')):
#-#    if _path not in sys.path:
#-#        sys.path.append(_path)
#-#import server_conf

def get_my_log(logname):
    global info, debug, error
    rlog = logging.getLogger()
    rlog.setLevel(logging.DEBUG)
    rlog.handlers = [_h for _h in rlog.handlers if not isinstance(_h, logging.StreamHandler)]

    log_sh = logging.StreamHandler()
    log_sh.setLevel(logging.INFO)
    fmt = logging.Formatter('%(asctime)s %(levelname)s %(name)s %(funcName)s %(lineno)d | %(message)s', '%H:%M:%S')  # LogFormatter()
    log_sh.setFormatter(fmt)
    rlog.addHandler(log_sh)  # add handler(s) to root loggerll

    logdir = os.path.join(_LOCAL_PATH_, 'log')
    if not os.path.exists(logdir):
        os.mkdir(logdir)
    logfile = os.path.join(logdir, logname)
    log_filehdl = logging.handlers.TimedRotatingFileHandler(logfile, when='midnight', backupCount=5)
    log_filehdl.setLevel(logging.DEBUG)
    fmt = logging.Formatter('%(asctime)s %(levelname)1.1s %(processName)s %(module)s %(funcName)s %(lineno)d | %(message)s', '%H:%M:%S')
    log_filehdl.setFormatter(fmt)
    rlog.addHandler(log_filehdl)  # add handler(s) to root logger
    rlog.info('log file %s %s', log_filehdl.baseFilename, log_filehdl.mode)
    return rlog


def flat_list(x):
    for _x in x:
        if isinstance(_x, (list, tuple)):
            for _f in _x:
                yield _f
        else:
            yield _x

