import logging

from sqlalchemy import Column, String, Float, ForeignKey, DateTime, func
from sqlalchemy.orm import relationship, scoped_session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base

from sqlalchemy import create_engine

logger = logging.getLogger(__name__)

engine = create_engine("sqlite:///foo.db")

from contextlib import contextmanager


@contextmanager
def db_session():
    session = scoped_session(sessionmaker(autocommit=False,
                                          autoflush=True,
                                          bind=engine))
    try:
        yield session
        session.commit()
    finally:
        session.close()

Base = declarative_base()
Base.query = scoped_session(sessionmaker(autocommit=False,
                                         autoflush=False,
                                         bind=engine)).query_property()


class Article(Base):
    __tablename__ = "article"

    url = Column(String, primary_key=True)
    images = relationship("Image", backref="article")
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    @property
    def score(self):
        scores = [i.score for i in self.images]
        return max(scores) if scores else 0

    def get_score(self):
        return max(i.score for i in self.images)

    @classmethod
    def by_url(cls, url):
         return cls.query.filter_by(url=url).first()

    @classmethod
    def create(cls, url):
        with db_session() as db:
            obj = cls(url=url)
            db.add(obj)


class Image(Base):
    __tablename__ = "image"

    url = Column(String, primary_key=True)
    score = Column(Float)
    article_id = Column(String, ForeignKey("article.url"))
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    @classmethod
    def by_url(cls, url):
         return cls.query.filter_by(url=url).first()

    @classmethod
    def create(cls, url, score, article_url):
        with db_session() as db:
            obj = cls(url=url, score=score, article_id=article_url)
            db.add(obj)


if __name__ == "__main__":
    Base.metadata.create_all(engine)
