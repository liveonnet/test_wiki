#coding=utf8
import os
import sys
reload(sys)
sys.setdefaultencoding('utf8')
from sqlalchemy import ForeignKey
from sqlalchemy import Table
from sqlalchemy import Column, Integer, String, Text
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

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
from lib.applog import app_log
info, debug, error = app_log.info, app_log.debug, app_log.error
#
#
#
# Page Tag
Base = declarative_base()
page_tag = Table('page_tags', Base.metadata,
                 Column('page_id', Integer, ForeignKey('pages.id')),
                 Column('tag_id', Integer, ForeignKey('tags.id'))
                 )


class Page(Base):
    __tablename__ = 'pages'
    id = Column(Integer, primary_key=True)
    content = Column(Text)
    size = Column(Integer)
    wiki_page_id = Column(Integer)
    tags = relationship('Tag', secondary=page_tag, order_by='Tag.weight.desc()', backref='pages', lazy='dynamic')

    def __init__(self, content, wiki_page_id):
        self.content = content
        self.wiki_page_id = wiki_page_id
        self.size = len(content)

    @hybrid_property
    def title(self):
        return [x for x in self.tags if x.weight == 99]

    def __repr__(self):
        return "<Page('%s', %d, %s)>" % (self.title, self.wiki_page_id, format(self.size, ','))


class Tag(Base):
    __tablename__ = 'tags'
    id = Column(Integer, primary_key=True)
    content = Column(String)
    weight = Column(Integer)

    def __repr__(self):
        return "<Tag('%s', %d, %d)>" % (self.content, self.id, self.weight)


if __name__ == '__main__':
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from IPython import embed
    engine = create_engine('sqlite:////home/kevin/data_bk/work/test_wiki/wiki.sqlite', echo=True)  # http://docs.sqlalchemy.org/en/rel_1_0/core/engines.html#database-urls
    Sess = sessionmaker(bind=engine)
    sess = Sess()
    t = sess.query(Tag).filter(Tag.id == 1).one()
    embed()
    sess.close()
