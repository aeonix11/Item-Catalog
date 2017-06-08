Overview
-------------
Item Catalog application made with Python, Flask and SQL ALCHEMY


Components
-------------
+ Routing and Templating made with Flask
+ Uses SQLAlchemy to communicate with the back-end db
+ RESTful API endpoints that return json files(One function is built into the website with a   	    button the other has to be accessed by manualy typing in the url with the category id and the item id. If you have setup the database and loaded the dummy content then you can use this example. http://localhost:5000/9/item/1/JSON)

+ Uses Google Login to authenticate users(for some reason not all gmail accounts show the name, I could not figure out why but it works perfectly on my main gemail account)

+ authenticated users can create and edit items
+ Front-end forms and webpages built with boostrap


Running the application
------------------------
First enter python database_setup.py into your console.
Secondly enter python catalog_item_fill.py to fill the database with dummy content.
Thirdly enter python application.py to run the application.
Fourthly open your browser on http://localhost:5000


Author
-------
Author: David Brink

