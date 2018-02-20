from sqlalchemy import Column, Integer, String, ForeignKey, Table
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, backref

BaseModel = declarative_base()

class User(BaseModel):
    __tablename__ = 'user'
    id = Column(Integer, primary_key=True)
    username = Column(String(150), nullable=False, unique=True)
    email = Column(String(254), unique=True)


group_profile_table = Table(
    'group_profile',
    BaseModel.metadata,
    Column('group_id', Integer, ForeignKey('group.id')),
    Column('profile_id', Integer, ForeignKey('profile.id'))
)


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
        backref=backref('profile', uselist=False,
                        cascade='all, delete-orphan'),
    )
    groups = relationship(
        "Group",
        secondary=group_profile_table,
        back_populates="members")

    def __init__(self, nickname=None, the_user=None, **kwargs):
        if nickname is not None and "name" not in kwargs:
            self.name = nickname
        if the_user is not None:
            self.user = the_user
        super(Profile, self).__init__(**kwargs)


class Group(BaseModel):
    __tablename__ = 'group'
    id = Column(Integer, primary_key=True)
    name = Column(String(150), nullable=False)

    members = relationship(
        "Profile",
        secondary=group_profile_table,
        back_populates="groups")
