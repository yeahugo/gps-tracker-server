from .adapter import Adapter
from models import Message
import re
import config

class tianqin(Adapter):

    @classmethod
    def decode(cls, datastring):
        #e.g. *HQ,4300248443,V1,160910,V,3958.7297,N,11621.6888,E,0.00,187,300314,FFE7FBFF#
        re_location_full = '^*HQ,(?P<imei>\d{10}),' + \
            'V1,(?P<local_time>\d{6})' + \
            '(?P<validity>[AV]),'+ \
            '(?P<latitude>\d+\.\+),' + \
            '(?P<latitude_hemisphere>[NS]),' + \
            '(?P<longitude>\d+\.\d+),' + \
            '(?P<longitude_hemisphere>)[EW],' + \
            '\d+,\d+,\W+#'

        if re.match(re_location_full,datastring):
            imei = re.match(re_location_full, datastring).group('imei')
            latitude = match.group('latitude')
            latitude_hemisphere = match.group('latitude_hemishpere')
            longitude = match.group('logitude')
            longitude_hemisphere = match.group('longitude_hemisphere')

            message = Message(imei=imei,message_type=config.MESSAGE_TYPE_LOCATION_FULL,message_datastring)

            re_location = '^(\d+)(\d{2}\.\d+)$'

            (h,m) = re.match(re_location, latitude).group
            h = float(h)
            m = float(m)
            latitude = h + m/60

            if 'S' == latitude_hemisphere
            latitude = -latitude

            (h,m) = re.match(re_location, longitude).group
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
            resp = 'HQ,{imei},V4,{cmd},time1'.format(imei=message.imei, cmd='B',message.time)
            return resp


