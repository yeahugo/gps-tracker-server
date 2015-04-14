from .adapter import Adapter
from models import Message
import re
import config
import time
import string
from binascii import *

text_characters = "".join(map(chr, range(32, 127))) + "\n\r\t\b"
_null_trans = string.maketrans("", "")
def isText(s, text_characters=text_characters, threshold=0.30):
    # if s contains any null, it's not text:
    if "\0" in s:
        return False
    # an "empty" string is "text" (arbitrary but reasonable choice):
    if not s:
        return True
    # Get the substring of s made up of non-text characters
    t = s.translate(_null_trans, text_characters)
    # s is 'text' if less than 30% of its characters are non-text ones:
    return len(t)/len(s) <= threshold

def handleFullLocation(datastring):
    #e.g. 2443002484430326031204153958713900116216801c000222ffe7fbffff0000
    re_location_full = '^\*HQ,(?P<imei>\d{10}),' + \
		   'V1,(?P<local_time>\d{6}),' + \
		   '(?P<validity>[AV]),'+ \
		   '(?P<latitude>\d+\.\d+),' + \
		   '(?P<latitude_hemisphere>[NS]),' + \
		   '(?P<longitude>\d+\.\d+),' + \
		   '(?P<longitude_hemisphere>)[EW],' + \
		   '(.+)#'

    if re.match(re_location_full,datastring):
	match = re.match(re_location_full, datastring)
	imei = match.group('imei')
	latitude = match.group('latitude')
	latitude_hemisphere = match.group('latitude_hemisphere')
	longitude = match.group('longitude')
	longitude_hemisphere = match.group('longitude_hemisphere')
	local_time = match.group('local_time')

	message = Message(imei=imei,message_type=config.MESSAGE_TYPE_LOCATION_FULL,message_datastring=datastring)

	re_text_location = '^(\d+)(\d{2}\.\d+)$'
	(h,m) = re.match(re_text_location, latitude).groups()
	latitude = float(h) + float(m)/60
	if 'S' == latitude_hemisphere:
	    latitude = -latitude

	(h,m) = re.match(re_text_location, longitude).groups()
	longitude = float(h) + float(m)/60
	if 'W' == longitude_hemisphere:
	    longitude = -longitude

	message.latitude = latitude
	message.longitude = longitude
        return message
    else:
	return None 

def handleBinaryLocation(datastring):
    datastring = hexlify(datastring) 
    logger.info('hexlify is %s' % datastring)
    re_location_full = '^(\d{2})(?P<imei>\d{10})' + \
			'(?P<local_time>\d{6})' + \
			'(?P<local_date>\d{6})' + \
			'(?P<latitude>\d{8})' + \
			'00' + \
			'(?P<longitude>\d{9})' + \
			'(?P<location_flag>\w)' + \
			'(?P<speed>\d{6})' + \
			'(?P<status>\w{8})' + \
			'(?P<alarm>\w{2})' + '0000'

    if re.match(re_location_full,datastring):
        match = re.match(re_location_full, datastring)
        imei = match.group('imei')
        latitude = match.group('latitude')
        longitude = match.group('longitude')

	location_flag = int(match.group('location_flag'),16)
	longitude_hemisphere = 'E' if location_flag&8!=0 else 'W' 
	latitude_hemisphere = 'N' if location_flag&4!=0 else 'S'
	location_validity = (location_flag&2!=0)

	if longitude_hemisphere == 'S':
	    longitude = -longitude
	if latitude_hemisphere == 'W':
	    latitude = -latitude

	message = Message(imei=imei,message_type=config.MESSAGE_TYPE_LOCATION_FULL,message_datastring=datastring)
	re_binary_location = '^(\d{2})(\d{6})$'
        (h,m) = re.match(re_binary_location,latitude).groups()
	latitude = float(h) + float(m)/10000/60 

	re_binary_longitude = '^(\d{3})(\d{6})$'
	(h,m) = re.match(re_binary_longitude,longitude).groups()
	longitude = float(h) + float(m)/10000/60
	message.latitude = latitude
	message.longitude = longitude
	message.validity = int(location_validity)
	return message
    else:
	return None

class tianqin(Adapter):
    delimiter = ';'

    @classmethod
    def decode(cls, datastring):
	print isText(datastring)
	if isText(datastring):
	    return handleFullLocation(datastring)
	else:
	    return handleBinaryLocation(datastring)
        #e.g. *HQ,4300248443,V1,160910,V,3958.7297,N,11621.6888,E,0.00,187,300314,FFE7FBFF#

    @classmethod
    def encode(cls, message):
        """
        message asking that device report location once
        #resp = '**,imei:{imei},{cmd}'.format(imei=imei, cmd='B')
        """
        if config.MESSAGE_TYPE_REQ_LOCATION == message.message_type:
            resp = 'HQ,{imei},V4,{cmd}'.format(imei=message.imei, cmd='B')
            return resp

    @classmethod
    def response_to(cls, message):
	if type(message) in [str, unicode]:
	    message = cls.decode(data)
	if not message:
	    return
        if config.MESSAGE_TYPE_LOCATION_FULL == message.message_type:
	    return 'I1'

