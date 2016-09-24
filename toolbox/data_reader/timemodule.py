# -*- coding: utf-8 -*-

import time
import datetime

EXCHANGE_RATE_TO_SECOND = {'MS': 0.001, 'S': 1, 'MIN': 60, 'H': 3600}
DEFAULT_FORMAT_STRING = ['%Y-%m-%d %H:%M:%S.%f', '%Y%m%d%H%M%S%f']


class DateTime(datetime.datetime):
    def timestamp(self, time_unit='MS'):
        exchange_rate = EXCHANGE_RATE_TO_SECOND[time_unit]
        return (time.mktime(self.timetuple()) + self.microsecond / 1000000.0) / exchange_rate

    @classmethod
    def fromtimetuple(cls, time_tuple):
        if len(time_tuple) > 6:
            return DateTime(*time_tuple[0:6])
        else:
            return DateTime(*time_tuple)

    @classmethod
    def fromstring(cls, date_string, format_string=None):
        if format_string is None:
            for format_string in DEFAULT_FORMAT_STRING:
                format_string = format_string[0:len(date_string) - 2]
                try:
                    return DateTime.strptime(date_string, format_string)
                except ValueError:
                    continue
            else:
                raise ValueError('date string \'%s\' does not match any of the default formats' % date_string)
        else:
            return DateTime.strptime(date_string, format_string)


def create_date_time(*args):
    # input value is time tuple
    if isinstance(args[0], (time.struct_time, tuple, list)):
        return DateTime.fromtimetuple(args[0])

    # input value is integers
    elif 3 <= len(args) <= 7 and all([isinstance(item, int) for item in args]):
        return DateTime(*args)

    # input value is string
    elif isinstance(args[0], basestring):
        return DateTime.fromstring(*args)

    elif isinstance(args[0], datetime.datetime):
        return DateTime.fromtimetuple(args[0].timetuple())
    # unpredictable conditions
    else:
        raise SyntaxError('Unsupported syntax')

#
# if __name__ == '__main__':
#     print DateTime.fromtimetuple(time.localtime()).timestamp('S')
#     print create_date_time(time.localtime()).timestamp('S')
#     print create_date_time(datetime.datetime(2015, 12, 1, 16, 1)).timestamp('S')
#     print create_date_time(2015, 12, 1, 16, 1).timestamp('S')
#     print DateTime.strptime('20151201160100', '%Y%m%d%H%M%S').timestamp('S')
#     print DateTime.fromstring('20151201160100').timestamp('S')
#     print DateTime.fromstring('2015-12-01 16:01:00').timestamp('S')
#     print create_date_time('2015-12-01 16:01:00').timestamp('S')
#     print create_date_time('20151201160100').timestamp('S')
