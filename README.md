# Whoosh template

This is a template for using [whoosh](https://whoosh.readthedocs.io/en/latest/intro.html) with a wordpress database and a Vue.JS frontend

The only pourpose of this project is to get you up and running with a new index system ASAP.


# How to use

```bash
pip install -r requirements.txt
```

Configure the main.py file with your database info, and run the server, by default a wordpress query is already written, but easily you can modify and use any kind of database with any kind of information.

```bash
python3 main.py
```

now we will index the database, so you go to 

> http://127.0.0.1:5000/createindex

(this may take a while) 

and now everything is ready, just go to [the home of local server](http://127.0.0.1:5000) and start playing arround :) 


Fell free to modify everything that is needed.


