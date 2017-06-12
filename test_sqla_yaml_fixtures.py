from sqlalchemy import create_engine
from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session
from sqlalchemy.orm import relationship, backref
import pytest

import sqla_yaml_fixtures


#################################################
# Sample schema used on tests

BaseModel = declarative_base()

class User(BaseModel):
    __tablename__ = 'user'
    id = Column(Integer, primary_key=True)
    username = Column(String(150), nullable=False, unique=True)
    email = Column(String(254), unique=True)

class Profile(BaseModel):
    __tablename__ = 'profile'
    id = Column(Integer, primary_key=True)
    name = Column(String(150), nullable=False)
    user_id = Column(
        ForeignKey('user.id', deferrable=True, initially='DEFERRED'),
        nullable=False,
        unique=True)
    user = relationship(
        'User', uselist=False,
        backref=backref('profile', uselist=False, cascade='all, delete-orphan'),
    )




#################################################

# fixtures based on
# https://gist.github.com/kissgyorgy/e2365f25a213de44b9a2
@pytest.fixture(scope="session")
def engine():
    return create_engine('sqlite://')

@pytest.fixture(scope='session')
def tables(engine):
    BaseModel.metadata.create_all(engine)
    yield
    BaseModel.metadata.drop_all(engine)

@pytest.fixture
def session(engine, tables):
    connection = engine.connect()
    # begin the nested transaction
    transaction = connection.begin()
    # use the connection with the already started transaction
    session = Session(bind=connection)

    yield session

    session.close()
    # roll back the broader transaction
    transaction.rollback()
    # put back the connection to the connection pool
    connection.close()


####################################################
# tests


class TestStore:
    def test_put_get(self):
        store = sqla_yaml_fixtures.Store()
        store.put('foo', 'bar')
        assert store.get('foo') == 'bar'

    def test_get_non_existent(self):
        store = sqla_yaml_fixtures.Store()
        assert pytest.raises(KeyError, store.get, 'foo')

    def test_duplicate_key_raises(self):
        store = sqla_yaml_fixtures.Store()
        store.put('foo', 'bar')
        assert pytest.raises(AssertionError, store.put, 'foo', 'second')

    def test_dotted_key(self):
        class Foo:
            bar = 52
        store = sqla_yaml_fixtures.Store()
        store.put('foo', Foo)
        assert store.get('foo.bar.__class__.__name__') == 'int'



def test_insert_simple(session):
    fixture = """
User:
  - username: deedee
    email: deedee@example.com
  - username: joey
    email: joey@example.commit
"""
    sqla_yaml_fixtures.load(BaseModel, session, fixture)
    users = session.query(User).all()
    assert len(users) == 2
    assert users[0].username == 'deedee'
    assert users[1].username == 'joey'


def test_insert_relation(session):
    fixture = """
User:
  - __key__: joey
    username: joey
    email: joey@example.com
Profile:
  - user: joey
    name: Jeffrey
"""
    sqla_yaml_fixtures.load(BaseModel, session, fixture)
    users = session.query(User).all()
    assert len(users) == 1
    assert users[0].profile.name == 'Jeffrey'
