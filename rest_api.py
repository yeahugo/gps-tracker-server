import json
import config
import sys
import re
from flask_cors import CORS
from gevent.pywsgi import WSGIServer
from flask import Flask, request
from werkzeug.exceptions import NotFound, Unauthorized, BadRequest
from models import *

app = Flask(__name__)
app.debug = True
app.config['CORS_HEADERS'] = ['Content-Type', 'X-API-KEY']
cors = CORS(app)


def check_auth():
    api_key = request.headers.get('X-API-KEY')
    print "api_key"+api_key
    if not api_key:
        raise Unauthorized()
    u = User.check_api_key(api_key)
    if not u:
        raise Unauthorized()
    return u


@app.route('/login', methods=['POST'])
def login():
    try:
        d = json.loads(request.data)
        email = d['email']
        password = d['password']
    except:
        raise BadRequest()
    try:
        u = User.objects.get(email=email)
    except (User.DoesNotExist, User.MultipleObjectsReturned):
        raise Unauthorized()
    if u.check_password(password):
        return json.dumps({
            'api_key'   : u.api_key,
            'email'     : u.email,
            'id'        : str(u.id),
        })
    raise Unauthorized()

@app.route('/user/register', methods=['POST'])
def user_register():
    try:
        d = json.loads(request.data)
        email = d['email']
        password = d['password']
    except:
        raise BadRequest()
    if not email or not password:
        raise BadRequest('Please supply both email and password')
    u = User(email=email, password=password)
    try:
        u.save()
    except mongoengine.NotUniqueError:
        raise BadRequest('User with that email already exists')
    except mongoengine.ValidationError:
        raise BadRequest('Bad email')
    return json.dumps({
        'api_key'   : u.api_key,
        'email'     : u.email,
        'id'        : str(u.id),
    })

@app.route('/device/<device_id>/messages', methods=['GET'])
def device_messages(device_id):
    user = check_auth()
    try:
        device = GPSDevice.objects.get(id=device_id)
    except (GPSDevice.DoesNotExist, mongoengine.ValidationError):
        raise NotFound()
    except GPSDevice.MultipleObjectsReturned:
        raise
    if device not in user.devices:
        raise Unauthorized()
    resp = []
    for message in device.messages:
        resp.append({
            'id'                : str(message.id),
            'message_type'      : message.message_type,
            'state'             : message.state,
            'imei'              : message.imei,
            'message_datastring': message.message_datastring,
            'latitude'          : str(message.latitude) if message.latitude else None,
            'longitude'         : str(message.longitude) if message.longitude else None,
            'created'           : message.created.isoformat(),
        })
    return json.dumps(resp)

@app.route('/device/<device_id>/trackOnce', methods=['POST'])
def device_track_once(device_id):
    user = check_auth()
    try:
        device = GPSDevice.objects.get(id=device_id)
    except (GPSDevice.DoesNotExist, mongoengine.ValidationError):
        raise NotFound()
    except GPSDevice.MultipleObjectsReturned:
        raise
    if device not in user.devices:
        raise Unauthorized()
    print 'IMEI %s requesting to trackOnce' % device.imei
    m = Message()
    m.imei = device.imei
    m.message_type = config.MESSAGE_TYPE_REQ_LOCATION
    m.save()
    return 'location request sent'

@app.route('/user/<user_id>', methods=['GET'])
@app.route('/user', methods=['GET'])
def user_list(user_id=None):
    user = check_auth()
    if user_id:
        try:
            u = User.objects.get(id=user_id)
        except:
            raise NotFound()
        resp = {
            '_id'       : str(u.id),
            'email'     : str(u.email),
            'devices'   : [str(d.id) for d in u.devices],
        }
    else:
        resp = []
        for u in User.objects.filter(id=user.id):
            resp.append({
                '_id'       : str(u.id),
                'email'     : str(u.email),
                'devices'   : [str(d.id) for d in u.devices],
		'animals'   : [str(a.id) for a in u.animals],
            })
    return json.dumps(resp)

@app.route('/device/<id>', methods=['DELETE'])
def delete_device(id):
    user = check_auth()
    try:
        device = GPSDevice.objects.get(id=id)
    except GPSDevice.DoesNotExist:
        raise NotFound()
    if user != device.user:
        raise NotFound()
    user.devices = filter(lambda x:x.id!=id, user.devices)
    user.save()
    device.delete()
    return 'ok'

@app.route('/animal/<id>',methods=['GET'])
def animal_detail():
    user = check_auth()
    try:
	animal = Animal.objects.get(id=id)
    except Animal.DoesNotExist:
	raise NotFound()
    if animal.device:
	raise NotFound()
    device = animal.device
    resp = {
	'id' 	: str(animal.id),
        'name'  : str(animal.name),
	'type'  : str(animal.animal_type),
	'sub_type':str(animal.sub_type),
	'gender': animal.gender,
	'birthday':str(animal.birthday),
	'latitude': device.latitude,
	'longitude':device.longitude,
	'location_time':device.location_time
    }
    return resp

@app.route('/animal',methods=['POST'])
def add_animal():
    user = check_auth()
    try:
	print request.data
	data = json.loads(request.data)
    except:
    	raise BadRequest()
    if not data.get('imei',None):
        raise BadRequest('imei required')
    try:
	device = GPSDevice.objects.get(imei=data['imei'])
        if device.user != user:
    	    raise BadRequest('There was a problem adding that device')
    except:
 	device = GPSDevice(imei=data['imei'])   
    animal = Animal()
    animal.animal_type = data['type']
    animal.gender = data['gender']
    animal.age = data['age']
    animal.name = data['name']
    animal.sub_type = data['sub_type']
    animal.device = device
    device.animal = animal
    user.animals.append(animal)
    animal.save()
    device.save()
    user.save()
    resp = {
	'id' : str(animal.id)
    }
    return resp

@app.route('/device', methods=['POST'])
def add_device():
    user = check_auth()
    try:
        print request.data
        print request
        data = json.loads(request.data)
    except:
        raise BadRequest()
    if not data.get('imei', None):
        raise BadRequest('imei required')
    if not re.match('^\d{8,15}$', data['imei']):
	print "imei length error"
        raise BadRequest('imei must be 15 digits long')
    try:
        device = GPSDevice.objects.get(imei=data['imei'])
        if device.user != user:
            raise BadRequest('There was a problem adding that device')
    except GPSDevice.DoesNotExist:
        data = {
            'imei'          : data.get('imei'),
            'vehicle_plate' : data.get('vehicle_plate', None),
        }
        device = GPSDevice(imei=data['imei'])
        device.save()
        user.devices.append(device)
        user.save()
    resp = {
        'id'    : str(device.id),
        'imei'  : device.imei,
    }
    return json.dumps(resp)

@app.route('/device/<device_id>', methods=['GET'])
@app.route('/device', methods=['GET'])
def devices(device_id=None):
    user = check_auth()
    if device_id:
        try:
            d = filter(lambda d:str(d.id)==device_id, user.devices)[0]
            resp = {
                'id'            : str(d.id),
                'name'          : d.name,
                'imei'          : d.imei,
                'ipaddr'        : d.ipaddr,
                'vehicle_plate' : d.vehicle_plate,
                'is_online'     : d.is_online,
                'latitude'      : str(d.latitude) if d.latitude else None,
                'longitude'     : str(d.longitude) if d.longitude else None,
                'icon'          : 'img/car-black.png'
            }
        except:
            raise NotFound()
    else:
        resp = []
        for device in user.devices:
            d = {
                'id'            : str(device.id),
                'imei'          : device.imei,
                'ipaddr'        : device.ipaddr,
                'is_online'     : device.is_online,
                'latitude'      : str(device.latitude) if device.latitude else None,
                'longitude'     : str(device.longitude) if device.longitude else None,
                'icon'          : 'img/car-black.png'
            }
            resp.append(d)
    return json.dumps(resp)

@app.route('/animal',methods=['GET'])
@app.route('/animal/<animal_id>',methods=['GET'])
def animals(animal_id=None):
    user = check_auth()
    if animal_id:
	try:
	    animal = filter(lambda a:str(d.id)==animal_id,user.animals)[0]
	    device = a.device
	    resp = {
		'id'		:str(animal.id),
		'name'		:animal.name,
		'birthday'	:animal.birthday,
		'type'		:animal.animal_type,
		'sub_type'	:animal.sub_type,
		'gender'	:animal.gender,
		'latitude'	:device.latitude,
		'longitude'	:device.longitude
	    }
	except:
	    raise NotFound()
    else:
	resp = []
	for animal in user.animals:
	    a = {
		'id'		:str(animal.id),
		'name'		:animal.name,
		'birthday'	:animal.birthday,
		'type'		:animal.animal_type,
		'sub_type'	:animal.sub_type,
		'gender'	:animal.gender,
		'latitude'	:device.latitude,
		'longitude'	:device.longitude
	    }
	    resp.append(a)
    return json.dumps(resp)

if __name__=='__main__':
    http = WSGIServer(('', 5001), app)
    http.serve_forever()
