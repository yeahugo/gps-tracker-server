from flask import Flask
from flask.ext import admin
from flask.ext.admin.contrib.mongoengine import ModelView
from werkzeug.contrib.fixers import ProxyFix
from flask.ext.mongoengine import MongoEngine

# Create application
app = Flask(__name__)

app.wsgi_app = ProxyFix(app.wsgi_app)

app.config['SECRET_KEY'] = '123456789'
app.config['MONGODB_SETTINGS'] = {'DB':'gpstrack'}

db = MongoEngine()
db.init_app(app)

class GPSDevice(db.Document):
    imei = db.StringField()
    ipaaddr = db.StringField()
    name = db.StringField()
    responses = db.ListField(db.StringField())
    latitude = db.DecimalField()
    longitude = db.DecimalField()

class Animal(db.Document):
    name = db.StringField(max_length=200)
    
class GPSView(ModelView):
    column_list = ['imei','name']

class AnimalView(ModelView):
    column_list = ('name')

class User(db.Document):
    email = db.StringField()

class UserView(ModelView):
    column_list = ['email']

@app.route('/index')
def index():
    return '<a href="/admin/">Click me to get to Admin!</a>'

if __name__ == '__main__':
    admin = admin.Admin(app,'Animal Admin')
#    AnimalView(Animal)
#    admin.add_view(AnimalView(Animal))
#    admin.add_view(GPSView(GPSDevice))
    admin.add_view(UserView(User))
    
    app.debug = True
    app.run('0.0.0.0',5003)
