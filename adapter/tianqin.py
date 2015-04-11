from .adapter import Adapter
from models import Message
import re
import config
import time

class tianqin(Adapter):
    delimiter = ';'

    @classmethod
    def decode(cls, datastring):
        #e.g. *HQ,4300248443,V1,160910,V,3958.7297,N,11621.6888,E,0.00,187,300314,FFE7FBFF#
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

            message = Message(imei=imei,message_type=config.MESSAGE_TYPE_LOCATION_FULL,message_datastring=datastring)

            re_location = '^(\d+)(\d{2}\.\d+)$'

            (h,m) = re.match(re_location, latitude).groups()
            h = float(h)
            m = float(m)
            latitude = h + m/60

            if 'S' == latitude_hemisphere:
            	latitude = -latitude

            (h,m) = re.match(re_location, longitude).groups()
            h = float(h)
            m = float(m)
            longitude = h + m/60
            if 'W' == longitude_hemisphere:
                longitude = -longitude

            message.latitude = latitude
            message.longitude = longitude

        else:
            return None
        return message

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
	print "message_type"+message.message_type
	if type(message) in [str, unicode]:
	    message = cls.decode(data)
	if not message:
	    return
        if config.MESSAGE_TYPE_LOCATION_FULL == message.message_type:
	    time_string = time.strftime('%H%M%S',time.localtime(time.time()))
	    resp = '*HQ,{imei},D1,{time},{interval},1'.format(imei=message.imei, time=time_string, interval='60')
	    return resp

