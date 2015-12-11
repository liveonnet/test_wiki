#coding=utf8
u'''
https://zh.wikipedia.org/wiki/Help:%E5%A6%82%E4%BD%95%E8%AE%BF%E9%97%AE%E7%BB%B4%E5%9F%BA%E7%99%BE%E7%A7%91
需要改hosts文件来访问zh.wikipedia.org
198.35.26.96 zh.wikipedia.org
198.35.26.108 zh.m.wikipedia.org
en.wikipedia.org则不需要

SELECT content, count(*) t FROM tags where weight=99 group by content having t > 1;
SELECT wiki_page_id, count(*) t FROM pages group by wiki_page_id having t > 1 order by t desc ;
'''

import sys
reload(sys)
sys.setdefaultencoding('utf8')
import os
import json
import re
import pycurl
from time import sleep
from collections import deque
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from tornado.gen import coroutine
from tornado.gen import Task
from tornado.httpclient import AsyncHTTPClient
from tornado.httpclient import HTTPRequest
from IPython import embed
embed

if __name__ == '__main__':
    _LOCAL_PATH = os.path.abspath(os.path.dirname(__file__))
    base_dir = os.path.abspath(os.path.join(_LOCAL_PATH, os.path.pardir))
    for _path in (base_dir,
                  os.path.join(base_dir, 'lib'),
                  os.path.join(base_dir, 'model'),
                  os.path.join(base_dir, 'script'),
                  ):
        print 'add path %s' % _path
        if _path not in sys.path:
            sys.path.append(_path)
from model.model import Base
from model.model import Tag
from model.model import Page
from initlog import get_my_log
logger = get_my_log('tw.log')
info, debug, error = logger.info, logger.debug, logger.error

#-#import requests
import requesocks as requests
from requesocks.exceptions import SSLError
#-#from requests.adapters import HTTPAdapter
#-#from requests.packages.urllib3.poolmanager import PoolManager

#-#import ssl
#-#from functools import wraps
#-#def sslwrap(func):
#-#    @wraps(func)
#-#    def bar(*args, **kw):
#-#        kw['ssl_version'] = ssl.PROTOCOL_TLSv1
#-#        return func(*args, **kw)
#-#    return bar
#-#
#-#ssl.wrap_socket = sslwrap(ssl.wrap_socket)


#-#class MyAdapter(HTTPAdapter):
#-#    def init_poolmanager(self, connections, maxsize, block=False):
#-#        self.poolmanager = PoolManager(num_pools=connections,
#-#                                       maxsize=maxsize,
#-#                                       block=block,
#-#                                       ssl_version=ssl.PROTOCOL_TLSv1)


#
#
#
engine = create_engine('sqlite:///./wiki.sqlite', echo=False)  # 定义引擎
#-## Page Tag
#-#Base = declarative_base()
#-#page_tag = Table('page_tags', Base.metadata,
#-#                 Column('page_id', Integer, ForeignKey('pages.id')),
#-#                 Column('tag_id', Integer, ForeignKey('tags.id'))
#-#                 )
#-##-#page_title = Table('page_titles', Base.metadata,
#-##-#                    Column('page_id', Integer, ForeignKey('pages.id')),
#-##-#                    Column('title_id', Integer, ForeignKey('titles.id'))
#-##-#                    )
#-#
#-#
#-#class Page(Base):
#-#    __tablename__ = 'pages'
#-#    id = Column(Integer, primary_key=True)
#-#    content = Column(Text)
#-#    size = Column(Integer)
#-#    wiki_page_id = Column(Integer)
#-#    tags = relationship('Tag', secondary=page_tag, order_by='Tag.weight.desc()', backref='pages')
#-#
#-#    def __init__(self, content, wiki_page_id):
#-#        self.content = content
#-#        self.wiki_page_id = wiki_page_id
#-#        self.size = len(content)
#-#
#-#    @hybrid_property
#-#    def title(self):
#-#        return [x for x in self.tags if x.weight == 99]
#-#
#-#    def __repr__(self):
#-#        return "<Page(title='%s', pid=%d, size=%d)>" % (self.title, self.wiki_page_id, self.size)
#-#
#-##-#class Title(Base):
#-##-#    __tablename__ = 'titles'
#-##-#    id = Column(Integer, primary_key=True)
#-##-#    content = Column(String)
#-##-#    weight = Column(Integer)
#-##-#
#-##-#    def __repr__(self):
#-##-#        return "<Title(content='%s', weight=%d)>" % (self.content, self.weight)
#-#
#-#
#-#class Tag(Base):
#-#    __tablename__ = 'tags'
#-#    id = Column(Integer, primary_key=True)
#-#    content = Column(String)
#-#    weight = Column(Integer)
#-#
#-#    def __repr__(self):
#-#        return "<Tag(content='%s', weight=%d)>" % (self.content, self.weight)
#-#

Base.metadata.create_all(engine)
info('table created.')

#-#    Session = sessionmaker(bind=engine)
Session = sessionmaker()
Session.configure(bind=engine)
sess = Session()
info('session created.')
#
#
#


class QueryObj(object):
    u'''
    https://zh.wikipedia.org/w/api.php?action=query&titles=Doesntexist|Main%20Page|Talk:&format=jsonfm
    '''
    USER_AGENT = 'KevinWikiCollector/0.1 (http://example.com/wikicollector/; liveonnet@qq.com) BasedOnTornado/4.1'
    URL_TITLES = 'https://zh.wikipedia.org/w/api.php?action=query&titles={title}&prop={prop}&rvprop={rvprop}&redirects&format=json&rvcontentformat=application/json&indexpageids='
    URL_TITLES = 'https://zh.wikipedia.org/w/api.php?action=query&titles={title}&prop={prop}&rvprop={rvprop}&redirects&format=json'
    DFT_TITLES = {'prop': 'revisions',
                  'rvprop': 'content',
                  }
#-#    URL_PAGES = 'https://zh.wikipedia.org/w/api.php?action=query&pageids={pageids}&redirects&format=json'
    URL_PAGES = 'https://zh.wikipedia.org/w/api.php?action=query&pageids={pageids}&prop={prop}&rvprop={rvprop}&redirects&format=json'
    DFT_PAGES = {}
#-#    URL_REV = 'https://zh.wikipedia.org/w/api.php?action=query&revids={revids}&redirects&format=json'
#-#    DFT_REV = {}

    def __init__(self, titles=None, pages=None, revisions=None):
        self.titles = titles
        self.pages = pages
        self.revisions = revisions
        self.real_url = None

    # http://stackoverflow.com/questions/22882667/socks-proxy-in-tornado-asynchttpclient
    @staticmethod
    def prepare_curl_socks5(curl):
        curl.setopt(pycurl.PROXYTYPE, pycurl.PROXYTYPE_SOCKS5)
        curl.setopt(pycurl.SSLVERSION, pycurl.SSLVERSION_SSLv3)

    @staticmethod
    @coroutine
    def getPageByTitleImpl1(titles, prop='revisions', rvprop='content', continue_from=None):
        AsyncHTTPClient.configure('tornado.curl_httpclient.CurlAsyncHTTPClient', defaults=dict(user_agent='KevinWikiCollector/0.1 (https://example.org/kevin/; liveonnnet@qq.com) BasedOnTornado/4.1'))
        url = QueryObj.URL_TITLES.format(title=titles, prop=prop, rvprop=rvprop)
        info('url: %s', url)
        http_client = AsyncHTTPClient()
        http_request = HTTPRequest(
            url,
            prepare_curl_callback=QueryObj.prepare_curl_socks5,
            proxy_host='127.0.0.1',
            proxy_port=1080,
            validate_cert=False,
        )
        response = yield Task(http_client.fetch, http_request)
        info(response.body)
        info(response.code)
        info(response.reason)
        info(response.headers)
        info(response.error)
        info(response.request.headers)
        info(QueryObj.getPagesData(response.body))

    @staticmethod
    def getPageByTitleImpl2(titles, prop='revisions', rvprop='content', continue_from=None):
        sess = requests.session()
#-#        sess.mount('https://', MyAdapter())
        sess.proxies = {'http': 'socks5://127.0.0.1:1080',
                        'https': 'socks5://127.0.0.1:1080',
                        }
        headers = {'User-Agent': 'KevinWikiCollector/0.1 (https://example.org/kevin/; liveonnnet@qq.com) BasedOnTornado/4.1',
                   'Accept-Language': 'zh-CN,zh;q=0.8,en-US;q=0.6,en;q=0.4;',
                   }
        url = QueryObj.URL_TITLES.format(title=titles, prop=prop, rvprop=rvprop)
        while 1:
#-#            info('code %s, encoding %s content-type %s', resp.status_code, resp.encoding, resp.headers['content-type'])
            try:
                resp = sess.get(url, headers=headers)
                d = QueryObj.getPagesData(resp.text)
                break
            except SSLError as e:
                info('got SSLError: %s', e)
                sleep(1.5)
            except Exception as e:
                info('got Exception: %s', e)
                sleep(1)
            info('url: %s', url)
        return d

    @staticmethod
    def getPageByPageId(pages, prop='revisions', rvprop='content', continue_from=None):
        sess = requests.session()
        sess.proxies = {'http': 'socks5://127.0.0.1:1080',
                        'https': 'socks5://127.0.0.1:1080',
                        }
        headers = {'User-Agent': 'KevinWikiCollector/0.1 (https://example.org/kevin/; liveonnnet@qq.com) BasedOnTornado/4.1',
                   'Accept-Language': 'zh-CN,zh;q=0.8,en-US;q=0.6,en;q=0.4;',
                   }
        url = QueryObj.URL_PAGES.format(pageids=pages, prop=prop, rvprop=rvprop)
        info('url: %s', url)
        resp = sess.get(url, headers=headers)
        info('code %s, encoding %s content-type %s', resp.status_code, resp.encoding, resp.headers['content-type'])
        d = QueryObj.getPagesData(resp.text)
        return d

    @staticmethod
    def getPagesData(data):
        d_rtn = {}

        if not data:
            return d_rtn
        jdata = json.loads(data)
        if 'query' not in jdata or 'pages' not in jdata['query']:
            return d_rtn

        d_rtn = {}
        for _pg_id, _pg_data in jdata['query'].iteritems():
            if 'title' in _pg_data:
                _k = _pg_data['title']
            else:
                _k = _pg_id
            d_rtn[_k] = _pg_data
        return d_rtn


@coroutine
def main_tornado():
    yield QueryObj.getPageByTitleImpl1(u'明')


def loadProgress():
    l_2get = []
    f_2get = os.path.join(os.path.dirname(__file__), 'q_2get.dat')
    try:
        l_2get = keyword_filter(json.loads(open(f_2get, 'rb').read()))
        info('loaded %d items from %s', len(l_2get), f_2get)
    except:
        pass

    f_nocontent = os.path.join(os.path.dirname(__file__), 'no_content.dat')
    st_no_content = set()
    try:
        st_no_content = set(json.loads(open(f_nocontent, 'rb').read()))
        info('loaded %d items from %s', len(st_no_content), f_nocontent)
    except:
        pass

    return l_2get, l_2get, st_no_content


def saveProgress(q_2get, st_no_content):
    l_2get = list(q_2get)
    f_2get = os.path.join(os.path.dirname(__file__), 'q_2get.dat')
    open(f_2get, 'wb').write(json.dumps(l_2get))
    info('saved %d items to %s', len(l_2get), f_2get)

    f_nocontent = os.path.join(os.path.dirname(__file__), 'no_content.dat')
    open(f_nocontent, 'wb').write(json.dumps(list(st_no_content)))
    info('saved %d items to %s', len(st_no_content), f_nocontent)


def keyword_filter(l_keyword):
    st_seen = set()
    rtn = []
    for x in l_keyword:
        if x not in st_seen:
            st_seen.add(x)
            if ':' in x:
                continue
            if not x.startswith((u'圖像', u':', u'<', u'{', u'[', u'File:', u'Category:', 'el:', 's:', 'wikt:')) \
               and ',' not in x and '/' not in x and '）' not in x and '%' not in x and '&' not in x:
                rtn.append(x)
    return rtn


def main(init_title):
    pTitle = re.compile(ur'\[\[([^\]]+?)\]\]')
    text_base_dir = os.path.join(os.path.dirname(__file__), 'data')
    if not os.path.exists(text_base_dir):
        info('create dir %s', text_base_dir)
        os.mkdir(text_base_dir)
    st_title_got = set()
    q_2get = deque()
    q_2get.append(init_title)

    l_2get, l_got, st_no_content = loadProgress()
    q_2get.extend(l_2get)
    st_title_got.update(l_got)
    del l_2get
    del l_got

    try:
        while 1:
            try:
                title = q_2get.popleft()
            except IndexError:
                info('no title to find, break')
                break

            info('\n%s\ngetting %s ...\n%s', '=' * 60, title, '=' * 60)
            l_title = title.split('|')  # <查询用名称>|<显示用名称>
            _query_title = l_title[0]

            if _query_title in st_no_content:
                info('\n%s\n\tSKIP no content %s\n%s', '-=' * 30, _query_title, '-=' * 30)
                # get page's keyword from db, then add to q_2get
                continue

            # check if exists in db
            if _query_title != init_title:
                _check_tag = sess.query(Tag).filter_by(content=_query_title, weight=99).first()
                if _check_tag and _check_tag.pages:
                    info('\n%s\n\tSKIP existing %s\n%s', '-=' * 30, _query_title, '-=' * 30)
                    # get page's keyword from db, then add to q_2get
                    continue

            # get title tags
            obj_title = []
            for _title in l_title:
                _tmp = sess.query(Tag).filter_by(content=_title, weight=99).first()
                if not _tmp:
                    _tmp = Tag(content=_title, weight=99)
    #-#                info('title created. %s', _tmp)
                obj_title.append(_tmp)

    #-#        if len(st_title_got) > 20:
    #-#            info('debug break ~~~')
    #-#            break

            d = QueryObj.getPageByTitleImpl2(_query_title)
            for _page_id, _page_info in d['pages'].iteritems():
    #-#            x = QueryObj.getPageByPageId(_page_id)
                if 'revisions' in _page_info:
                    for _i, _page in enumerate(_page_info['revisions'], 1):
                        assert _page['contentmodel'] == 'wikitext'
                        assert _page['contentformat'] == 'text/x-wiki'
                        if '*' in _page:
                            _text = _page['*']
                            # save content to disk file
                            _f_out = os.path.join(text_base_dir, _query_title + '.txt')
                            if not os.path.exists(_f_out):
                                open(_f_out, 'w').write(_text)
    #-#                            info('file created. %s', _f_out)

                            st_title_got.update(l_title)

                            # find keyword
                            l_keyword = pTitle.findall(_text)
                            l_keyword = keyword_filter(l_keyword)
                            # get keyword tags
                            st_str_tag = set()
                            for _keyword in l_keyword:
                                # 干支#干支紀年|干支紀年
                                _keyword = set(_keyword.replace(u'#', u'|').replace(u' ', u'_').split(u'|'))
                                for _real_tag in _keyword:
                                    if not _real_tag.strip():
                                        continue
                                    st_str_tag.add(_real_tag)
    #-#                            if any( x for x in st_str_tag if u'#' in x):
    #-#                                info('#################')
    #-#                                embed()

                            # add un-get title to queue
    #-#                        info('rev_%02d pageid %s title: \'%s\' len: %d keyword: %d', _i, _page_id, _page_info['title'], len(_text), len(l_keyword))
                            st_new_title = st_str_tag - st_title_got
                            q_2get.extend(st_new_title)
                            info('%+d, total/got/2get %d/%d/%d', len(st_new_title), len(st_title_got) + len(q_2get), len(st_title_got), len(q_2get))

                            # check if exists in db
                            _check_tag = sess.query(Tag).filter_by(content=_query_title, weight=99).first()
                            if _check_tag and _check_tag.pages:
                                info('SKIP existing title %s', _query_title)
                                continue

                            # create page obj
                            obj_tag = []
                            for _real_tag in st_str_tag:
                                    _tmp = sess.query(Tag).filter_by(content=_real_tag, weight=49).first()
                                    if not _tmp:
                                        _tmp = Tag(content=_real_tag, weight=49)
                                    obj_tag.append(_tmp)
                            obj_page = Page(content=_text, wiki_page_id=_page_id)
                            obj_page.tags = obj_title + obj_tag
                            sess.add(obj_page)
                            sess.commit()
                            info('page created. %s', obj_page)
                        else:
                            info('no content in pageid %s ???', _page_id)
                else:
                    info('no content for title %s', _query_title)
                    st_no_content.add(_query_title)

    finally:
        sess.flush()
        saveProgress(q_2get, st_no_content)

#-#    embed()

if __name__ == '__main__':
#-#    tornado.ioloop.IOLoop.instance().run_sync(main_tornado)
#-#    main(u'曆法')
    try:
        main(u'明朝')
    except KeyboardInterrupt:
        info('got KeyboardInterrupt')
