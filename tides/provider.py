from abc import ABC, abstractmethod

from datetime import datetime
import requests


class TideProvider(ABC):
    __registry = {}

    def __init_subclass__(cls, key, *args, **kwargs):
        super().__init_subclass__(*args, **kwargs)
        cls.__registry.update({key: cls})

    @classmethod
    def get_provider(self, provider, api_key):
        cls = self.__registry.get(provider)
        return cls(api_key)

    @abstractmethod
    def get_all_stations():
        pass


class AdmiraltyTideProvider(TideProvider, key='admiralty'):

    def __init__(self, api_key):
        self.name = 'admiralty'
        self.base_url = 'https://admiraltyapi.azure-api.net/uktidalapi/api/V1/'
        self.api_key = api_key

    @property
    def name(self):
        return self.__name

    @name.setter
    def name(self, name):
        self.__name = name

    @property
    def api_key(self):
        return self.__api_key

    @api_key.setter
    def api_key(self, key):
        self.__api_key = key

    def get_all_stations(self):
        response = self.__call("Stations")
        result = {"response": {}, "errors": []}
        for item in response.get("features"):
            result["response"].update({
                item["properties"]["Name"]: {
                    "id": item["properties"]["Id"],
                    "country": item["properties"]["Country"],
                    "long": item["geometry"]["coordinates"][0],
                    "lat": item["geometry"]["coordinates"][1],
                }
            }
            )
        return result

    def get_station_by_id(self, station_id):
        response = self.__call("Stations/{}".format(station_id))
        result = {"response": {}, "errors": []}
        result["response"].update({
            response["properties"]["Name"]: {
                "id": response["properties"]["Id"],
                "country": response["properties"]["Country"],
                "long": response["geometry"]["coordinates"][0],
                "lat": response["geometry"]["coordinates"][1],
            }
        }
        )
        return result

    def get_station_by_name(self, name):
        response = self.__call("Stations?name={}".format(name))
        result = {"response": {}, "errors": []}
        result["response"].update({
            response["features"][0]["properties"]["Name"]: {
                "id": response["features"][0]["properties"]["Id"],
                "country": response["features"][0]["properties"]["Country"],
                "long": response["features"][0]["geometry"]["coordinates"][0],
                "lat": response["features"][0]["geometry"]["coordinates"][1],
            }
        }
        )
        return result

    def get_tides(self, station=None, duration='1'):
        station_id = self.__get_station_id(station)
        tides = self.__call("Stations/{}/TidalEvents?duration={}".format(station_id, duration))
        return tides

    def next_tide(self, station=None):
        station_id = self.__get_station_id(station)
        tides = self.__call("Stations/{}/TidalEvents?duration={}".format(station_id, 2))
        current_dt = datetime.utcnow()

        for i in range(len(tides)):
            raw_dt = tides[i].get("DateTime")
            parsed_dt = raw_dt.split(".")[0]
            tide_dt = datetime.strptime(parsed_dt, "%Y-%m-%dT%H:%M:%S")

            if current_dt < tide_dt:
                return tides[i]

            if tide_dt.day > current_dt.day:
                return tides[i]

    def __call(self, endpoint):
        response = requests.get(self.base_url + endpoint,
                                headers={'Ocp-Apim-Subscription-Key': self.api_key}
                                )
        return response.json()

    def __get_station_id(self, station):
        response = self.__call("Stations?name={}".format(station))
        return response["features"][0]["properties"]["Id"]
