# -*- coding: utf-8 -*-
from sqlalchemy import *
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Item, Category, User

engine = create_engine('sqlite:///catalog_database.db')

Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
session = DBSession()

# Clear the tables
session.query(Category).delete()
session.query(Item).delete()
session.query(User).delete()
session.commit()

# Add categories
categories = ['Soccer', 'Basketball', 'Baseball', 'Frisbee', 'Snowboarding', 'Rock Climbing', 'Foosball', 'Skating', 'Hockey']

for category_name in categories:
    category = Category(name=category_name)
    session.add(category)
session.commit()

# Add users
User1 = User(name='Robo Barista', email='tinnyTim@udacity.com')
User2 = User(name='Aeonix', email='davidjbrink@gmail.com')
session.add(User1)
session.add(User2)
session.commit()

# Add items

item1 = Item(title='Stick', description='An ice hockey stick is a piece of equipment used in ice hockey to shoot, pass, and carry the puck across the ice. Ice hockey sticks are approximately 5cm long, composed of a long, slender shaft with a flat extension at one end called the blade.', category_id='9', user_id='1')
session.add(item1)

item2 = Item(title='Goggles', description='Make sure the model you plump for has a good amount of ventilation to reduce the instances of fogging when you get the perilous condition known as Big Sweaty Head, and that the frame you settle for gives you the most unobstructed vision certain models are bigger than others, just as certain people prefer their frames bigger than others. Another thing to bear in mind is many of the higher-priced models now offer solutions to make swapping lenses super easy, while some even have ones that automatically brighten or darken depending on cloud cover.', category_id='5', user_id='2')
session.add(item2)

item3 = Item(title='Frisbee', description='A frisbee is a disc-shaped gliding toy or sporting item that is generally plastic and roughly centimetres in diameter with a lip, used recreationally and competitively for throwing and catching, for example, in flying disc games. The shape of the disc, an airfoil in cross-section, allows it to fly by generating lift as it moves through the air while spinning.', category_id='4', user_id='1')
session.add(item3)
session.commit()
