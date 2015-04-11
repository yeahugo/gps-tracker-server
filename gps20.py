import re
import config
from .adapter import Adapter
from models import Message

class gps20(Adapter):
    delimiter = '.'

    @classmethod
    def decode(cls,datastring):
        re_location_full = '^\((?P<imei>)\d{12}\)' + \
            '(?P<command>\W{2}\d{2})' + \
            '(?P<date>\d{6})' + \
            '(?P<validity>[AV])' + \
            '(?P<latitude>\d+\.\d+)' + \
            '(?P<latitude_hemisphere>[NS])' + \
            '(?P<longitude>\d+\.\d+)' + \
            '(?P<longitude_hemisphere>[EW])' + \
            '(?P<speed>\d{3}\.\d{1})' + \
            '(?P<date_time>\d{6})' + \
            '(?P<io_state>\d\.\d{6})' + \
            '(?P<mile_post>\d{6}L)' + \
            '(?P<mile_data>\d{8})'

        if re.match(re_location_full, datastring):
            match = re.match(re_location_full, datastring):
            imei = match.group('imei')
            message = Message(imei=imei, message_type=config.MESSAGE_TYPE_LOCATION_FULL)

            latitude = match.group('latitude')
            latitude_hemisphere = match.group('latitude_hemisphere')
            longitude = match.group('longitude')
            longitude_hemisphere = match.group('longitude_hemisphere')

            re_location = '^(\d+)(\d{2}\.\d+)$'
            (h, m) = re.match(re_location, latitude).groups()
            h = float(h)
            m = float(m)
            latitude = h + m/60
            if 'S' == latitude_hemisphere:
                latitude = -latitude

            (h, m) = re.match(re_location, longitude).groups()
            h = float(h)
            m = float(m)
            longitude = h + m/60
            if 'W' == longitude_hemisphere:
                longitude = -longitude

            message.latitude = latitude
            message.longitude = longitude

