from flask import Flask
from models import *
from flask.ext import admin
from flask.ext.admin.contrib.mongoengine import ModelView


# Create application
app = Flask(__name__)

app.wsgi_app = ProxyFix(app.wsgi_app)

app.config['SECRET_KEY'] = '123456789'
app.config['MONGODB_SETTINGS'] = {'DB':'gpstrack'}

class AnimalView(ModelView):
    column_filters = ['name']

if __name__ == '__main__':
    admin = admin.Admin(app,'Animal Admin')
    admin.add_view(AnimalView(Animal))
    
    app.debug = True
    app.run('0.0.0.0')
