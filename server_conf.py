#coding=utf8
import os
import re
#-#from collections import defaultdict
from pprint import pformat


G_CONF = None
G_DB_CONF = None
G_REDIS_CONF = None

def getLockEnv(l_f):
    d = {}
#-#    d['db_stat_port'] = 3306 # default 
    for _f in l_f:
        if os.path.exists(_f):
            d.update( dict(  (k.strip(),v.strip('\'" \r')) for k,v in (x.split('=',1) for x in open(_f).read().split('\n') if x.strip() and not x.strip().startswith('#') ) ) )
        else:
            print('file not exists %s'%_f)
    return d

def loadConfig():
    global G_CONF, G_DB_CONF, G_REDIS_CONF
    if G_CONF:
        return
    LOCAL_DIR = os.path.dirname(os.path.abspath(__file__))
#-#    print('LOCAL_DIR %s'%LOCAL_DIR)
    f_config = os.path.join(LOCAL_DIR, 'server.conf')
    G_CONF = getLockEnv((f_config,))
#-#    print('all conf: %s'%pformat(G_CONF))
   
#-#    x = '|'.join(G_CONF['db_host_name_list'].split(','))
    p = re.compile(r'^db_(.+?)_(host|port|uname|upass|name)$', re.S)
    pdefault = re.compile(r'^db_(host|port|uname|upass|name)$', re.S)
    G_DB_CONF = {'default':{} }
    l_2del = []
    for _k,_v in G_CONF.iteritems():
        m = p.match(_k)
        if m:
            l_2del.append(_k)
            name = m.group(1)
            if name not in G_DB_CONF:
                G_DB_CONF[name] = {}
            G_DB_CONF[name][m.group(2)] = _v
        else:
            m = pdefault.match(_k)
            if m:
                l_2del.append(_k)
                G_DB_CONF['default'][m.group(1)] = _v 
#-#    print('db_conf: %s'%pformat(G_DB_CONF))

    p = re.compile(r'^redis_(.+?)_(host|port|db)$', re.S)
    pdefault = re.compile(r'^redis_(host|port|db)$', re.S)
    G_REDIS_CONF = {'default':{} }
    for _k,_v in G_CONF.iteritems():
        m = p.match(_k)
        if m:
            l_2del.append(_k)
            name = m.group(1)
            if name not in G_REDIS_CONF:
                G_REDIS_CONF[name] = {}
            G_REDIS_CONF[name][m.group(2)] = _v
        else:
            m = pdefault.match(_k)
            if m:
                l_2del.append(_k)
                G_REDIS_CONF['default'][m.group(1)] = _v 
#-#    print('redis_conf: %s'%pformat(G_REDIS_CONF))

    for _k in l_2del:
        G_CONF.pop(_k)
#-#    print('remain conf: %s'%pformat(G_CONF))

#-#x = os.path.join( os.path.dirname(os.path.abspath(__file__)), 'server.conf')
#-#app.config.from_object(loadConfig())
loadConfig()
#-#embed()
