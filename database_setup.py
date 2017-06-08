import os
import sys
from sqlalchemy import Column, ForeignKey, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine
import datetime

Base = declarative_base()

def get_current_time():
    return datetime.datetime.now()

# Create user
class User(Base):
    __tablename__ = 'user'
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    email = Column(String, nullable=False)
    picture = Column(String(250))

# Create Category
class Category(Base):
    __tablename__ = 'category'
    id = Column(Integer, primary_key=True)
    name = Column(String(80), nullable=False)
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship(User)

    @property
    def serialize(self):
        """Return serializeable format of the Category Object"""
        return {
            'name'    : self.name,
            'id'      : self.id,
            'user_id' : self.user_id
        }

# Create category item
class Item(Base):
    __tablename__ = 'item'

    id = Column(Integer, primary_key=True)
    title = Column(String(80), nullable=False)
    description = Column(String(250), nullable=False)
    date = Column(DateTime, default=get_current_time,
        onupdate=get_current_time)
        # automatically updates on creation and update
    category_id = Column(Integer, ForeignKey('category.id'))
    category = relationship(Category)
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship(User)

    @property
    def serialize(self):
        """Return serializeable format of the CategoryItem Object"""
        return {
            'id'           : self.id,
            'title'        : self.title,
            'description'  : self.description,
        }

engine = create_engine('sqlite:///catalog_database.db')

Base.metadata.create_all(engine)