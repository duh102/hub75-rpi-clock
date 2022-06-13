import datetime
import re
import tzlocal
import os
import json
from noaa_sdk import NOAA


class PredictionDataPoint(object):
    def __init__(self, value, time):
        self.value = value
        self.time = time

    def is_timely(self, now, prediction_endpoint):
        return now <= self.time <= prediction_endpoint

    def get_time(self):
        return self.time

    def get_value(self):
        return self.value

    def get_value_f(self):
        return 1.8 * self.value + 32


class PredictionSeries(object):
    def __init__(self, data_points=None):
        if data_points is None:
            data_points = []
        self.data_points = data_points

    def add_data_point(self, dp):
        self.data_points.append(dp)
        self.data_points.sort(key=lambda d: d.get_time())

    def get_value_at(self, time):
        sel_dp = self.data_points[0]
        for dp in self.data_points:
            if dp.get_time() > time:
                break
            sel_dp = dp
        return sel_dp

    def get_data_points(self):
        return list(self.data_points)


class WeatherPredictionData(object):
    __iso_pat = re.compile(
        r'(?P<timestamp>[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2})(?P<timezone>[\+-][0-9]{2}:[0-9]{2})(/P.+)?')

    prediction_length = datetime.timedelta(hours=48)

    # Extracts the timestamp from a duration, discarding the duration
    @classmethod
    def __duration_timestamp(cls, in_str, tz):
        mat = cls.__iso_pat.match(in_str)
        if mat is None:
            return None
        time_str = mat.group('timestamp')
        time_zone = mat.group('timezone').replace(':', '')
        return datetime.datetime.strptime('{}{}'.format(time_str, time_zone), '%Y-%m-%dT%X%z').astimezone(tz)

    def __init__(self, weather_data, timezone):
        now = datetime.datetime.now(timezone)
        if weather_data is None:
            self.last_updated = now - self.prediction_length  # If we have no data, assume our prediction is old
            self.precipitation = PredictionSeries()
            self.temperature = PredictionSeries()
            self.humidity = PredictionSeries()
            return

        self.last_updated = self.__duration_timestamp(weather_data['updateTime'], timezone)
        temp_dict = {
            'probabilityOfPrecipitation': PredictionSeries(),
            'temperature': PredictionSeries(),
            'relativeHumidity': PredictionSeries()
        }
        time_limit = now + self.prediction_length
        for key, series in temp_dict.items():
            # weather_data[key] looks like
            # "temperature": { << Key
            #     "uom": "wmoUnit:degC",
            #     "values": [
            #         {
            #             "validTime": "2022-06-12T05:00:00+00:00/PT1H",
            #             "value": 21.666666666666668
            #         }, ...
            #     ]
            # The uom changes depending on the data;
            # For temp it's degrees C
            # For humidity + precipitation it's % (relative humidity and probability)
            for measure_value in weather_data[key]['values']:
                ts = self.__duration_timestamp(measure_value['validTime'], timezone)
                if ts > time_limit:
                    continue
                value = measure_value['value']
                series.add_data_point(PredictionDataPoint(value, ts))

        self.precipitation = temp_dict['probabilityOfPrecipitation']
        self.temperature = temp_dict['temperature']
        self.humidity = temp_dict['relativeHumidity']

    def get_last_updated(self):
        return self.last_updated

    def get_temp_data(self):
        return self.temperature

    def get_humidity_data(self):
        return self.humidity

    def get_precipitation_data(self):
        return self.precipitation


class WeatherCache(object):
    cache_file = 'weather_cache.json'
    cache_length = datetime.timedelta(hours=23)

    def __init__(self, zip_code=None, country=None, tz=None):
        if zip_code is None:
            zip_code = '27529'
        if country is None:
            country = 'US'
        if tz is None:
            tz = tzlocal.get_localzone()
        self.zip_code = zip_code
        self.country = country
        self.tz = tz
        self.weather_data = None
        self.weather_prediction_data = None

    def get_current_prediction(self):
        if self.weather_data is None:
            if os.path.isfile(self.cache_file):
                try:
                    with open(self.cache_file, 'r') as infil:
                        self.weather_data = json.load(infil)
                        self.weather_prediction_data = WeatherPredictionData(self.weather_data, self.tz)
                except Exception as e:
                    print('Unable to load weather data from {:s}: {:s}'.format(os.path.abspath(self.cache_file), str(e)))
        if self.weather_data is None or self._cache_too_old():
            self.weather_data = self._retrieve_weather_immediate()
            self.weather_prediction_data = WeatherPredictionData(self.weather_data, self.tz)
        try:
            with open(self.cache_file, 'w') as outfil:
                json.dump(self.weather_data, outfil)
        except Exception as e:
            print('Unable to cache weather data to {:s}: {:s}'.format(os.path.abspath(self.cache_file), str(e)))
        return self.weather_prediction_data

    def _retrieve_weather_immediate(self):
        try:
            noaa = NOAA()
            return noaa.get_forecasts(self.zip_code, self.country, type='forecastGridData')
        except Exception as e:
            print('Couldn\'t retrieve weather data: {:s}'.format(str(e)))
            return None

    def _cache_too_old(self):
        if self.weather_prediction_data is None:
            return True
        local_now = datetime.datetime.now(self.tz)
        return self.weather_prediction_data.get_last_updated() + self.cache_length < local_now


