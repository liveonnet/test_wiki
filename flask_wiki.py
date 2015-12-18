#coding=utf8
from __future__ import print_function
#-#from gevent import monkey; monkey.patch_all()
#-#import os
import sys
reload(sys)
sys.setdefaultencoding('utf8')
#-#import pymysql
import logging
#-#from random import randint
import json
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from flask import Flask
from flask import url_for
from flask import render_template
from flask import make_response
#-#from flask import url_for
#-#from flask import request
from flask import g
#-#from flask import redirect
#-#from flask import abort
#-#from flask import flash
#-#from flask import session
#-#from IPython import embed
#-#from server_conf import G_CONF

DAEMON = 'wiki_api'
try:
    import setproctitle
except ImportError as e:
    print('import error %s' % e)
else:
    setproctitle.setproctitle(DAEMON)  # change process name...

from lib.tools import pcformat
pcformat
#-#from model.model import Page
from model.model import Tag
#-#from model.model import page_tag
from lib.langconv import Converter
from lib.applog import app_log
info, debug, error = app_log.info, app_log.debug, app_log.error
#-#from mysql_wrapper import DBWrapper4DBUtlis as DBWrapper
#-#from mysql_wrapper import DBWrapper4Simple as DBWrapper
#-#from lib.mysql_wrapper import DBWrapper4SqlAlchemyPool as DBWrapper

app = Flask(__name__)
app.logger.setLevel(logging.DEBUG)


class DBWrapper(object):
    Engine = None
    Sess = None

    def __init__(self, app_log):
        self.logger = app_log
        self.__class__.init()
        self.sess = None

    @staticmethod
    def init():
        if not DBWrapper.Engine:
            DBWrapper.Engine = create_engine('sqlite:////home/kevin/data_bk/work/test_wiki/wiki.sqlite', encoding='utf8', echo=False)  # http://docs.sqlalchemy.org/en/rel_1_0/core/engines.html#database-urls
            DBWrapper.Sess = sessionmaker(bind=DBWrapper.Engine)

    def close(self):
        if self.sess:
            self.sess.close()
#-#        if self.__class__.Engine:
#-#            self.__class__.Engine.close()

    def get_session(self):
        if self.sess is None:
            assert self.__class__.Sess
            self.sess = self.__class__.Sess()
        return self.sess


@app.before_request
def before_request():
#-#    print('before_request')
    pass
#-#    g.db = DBWrapper(app_log, pymysql)
    g.db = DBWrapper(app_log)
    g.sess = g.db.get_session()


@app.after_request
def after_request(resp):
#-#    print('after_request')
    db = getattr(g, 'db', None)
    if db:
        db.close()
    return resp


@app.teardown_request
def teardown_request(exception):
#-#    print('teardown_request %s' % exception)
    db = getattr(g, 'db', None)
    if db:
        db.close()
#-#    g.db.close()


item_per_page = 50

#
# handlers
#


@app.route('/t')
def test_wx_handler():
    return render_template('index.html')


@app.route('/')
def main_handler():
    info('ok')
    page_id = 1
    start = item_per_page * (page_id - 1)
    tags = g.sess.query(Tag).filter(Tag.weight == 99).order_by(Tag.id)[start:start + item_per_page]
    l = [(_x.content, url_for('title', title_id=_x.id)) for _x in tags]
    return render_template('main_new.html', l=l, content='no content now')


#-#@app.route('/title/s/', defaults={'page_title': ''})
@app.route('/title/s/<string:page_title>')
def titlelist_search(page_title):
    info('search title %s', page_title)
    tags = g.sess.query(Tag).filter(Tag.weight == 99).filter(Tag.content.like('%%%s%%' % page_title)).order_by(Tag.id)
    l = [(_x.content, url_for('title', title_id=_x.id)) for _x in tags]
    info('return %s matched title(s)', len(l))
    return json.dumps({'code': 1, 'titles': l}, ensure_ascii=False, separators=(',', ':'))


@app.route('/title/p/', defaults={'page_id': 1})
@app.route('/title/p/<int:page_id>')
def titlelist_page(page_id):
    raise NotImplementedError('废弃接口')
    info('page_id %s', page_id)
#-#    from sqlalchemy.ext.automap import automap_base
#-#    Base = automap_base()
#-#    Base.prepare(g.db.Engine, reflect=True)
#-#    Tag = Base.classes.tags
    start = item_per_page * (page_id - 1)
    tags = g.sess.query(Tag).filter(Tag.weight == 99).order_by(Tag.id)[start:start + item_per_page]
    l = [(_x.content, url_for('title', title_id=_x.id)) for _x in tags]
    info('len(l) %s', len(l))
    return json.dumps({'titles': l}, ensure_ascii=False, separators=(',', ':'))


@app.route('/title/f/', defaults={'from_title_id': 1})
@app.route('/title/f/<int:from_title_id>')
def titlelist_from(from_title_id):
    info('from_title_id %s', from_title_id)
    tags = g.sess.query(Tag).filter(Tag.id > from_title_id).filter(Tag.weight == 99).order_by(Tag.id)[:item_per_page]
    l = [(_x.content, url_for('title', title_id=_x.id)) for _x in tags]
    info('return %s title(s)', len(l))
    return json.dumps({'titles': l}, ensure_ascii=False, separators=(',', ':'))


@app.route('/title/<int:title_id>')
def title(title_id):
    info('The title page %s', title_id)
    title = g.sess.query(Tag).filter(Tag.id == title_id).one_or_none()
    if title:
        page = title.pages[0]
        return json.dumps({'code': 1,
                           'type': 'page',
                           'content': Converter('zh-hans').convert(page.content.decode('utf8')).encode('utf8'),  # .replace('\n', '<br/>'),
                           'tags': [{'url': url_for('tag', tag_id=_t.id), 'content': _t.content, 'weight': _t.weight} for _t in page.tags.order_by(Tag.id)[:item_per_page]],
                           'size': page.size,
                           'id': page.id,
                           }
                          )
    else:
        return json.dumps({'code': 0})


#-#@app.route('/content/', defaults={'content_id': -1})
#-#@app.route('/content/<int:content_id>')
#-#def content(content_id):
#-#    pass
#-##-#    return render_template('frame_content.html', content='The content page %s' % content_id)


@app.route('/tag_in_content/<int:title_id>/f/<int:from_tag_id>')
def taglist_from(title_id, from_tag_id):
    u'''获取内容包含的一部分tag
    内容的标题id 为 `title_id` ，要返回的tag是id 大于`from_tag_id` 的一部分
    '''
    info('tag for page %s from %s', title_id, from_tag_id)
    title = g.sess.query(Tag).filter(Tag.id == title_id).one_or_none()
    if title:
        page = title.pages[0]
        tags = page.tags.filter(Tag.id > from_tag_id).order_by(Tag.id)[:item_per_page]
        info('return %s tag(s)', len(tags))
        return json.dumps({'code': 1,
                           'type': 'tag_in_content',
                           'tags': [{'url': url_for('tag', tag_id=_t.id), 'content': _t.content, 'weight': _t.weight} for _t in tags],
                           }
                          )
    else:
        return json.dumps({'code': 0})


@app.route('/tag_in_content/', defaults={'tag_id': -1})
@app.route('/tag_in_content/<int:tag_id>')
def tag(tag_id):
    info('tag in content tag_id %s', tag_id)
    tag = g.sess.query(Tag).filter(Tag.id == tag_id).one_or_none()
    if tag:
        title = g.sess.query(Tag).filter(Tag.weight == 99).filter(Tag.content == tag.content).one_or_none()
        if title:
            page = title.pages[0]
            info('tag page size: %s', page.size)
            return json.dumps({'code': 1,
                               'type': 'page',
                               'content': Converter('zh-hans').convert(page.content.decode('utf8')).encode('utf8'),  # .replace('\n', '<br/>'),
                               'tags': [{'url': url_for('tag', tag_id=_t.id), 'content': _t.content, 'weight': _t.weight} for _t in page.tags],
                               'size': page.size,
                               'id': page.id,
                               }
                              )
        else:
            return json.dumps({'code': 0, 'content': u'没有内容'})
    else:
        return json.dumps({'code': 0, 'content': u'没有内容'})
#-#    return 'The tag page %s' % tag_id


@app.route('/about')
def about():
    return 'The about page'


@app.errorhandler(404)
def page_not_found(error):
    resp = make_response('', 404)
    resp.headers['ERR'] = 'user not found'
    info('return 404')
    return resp


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8888, debug=True)
