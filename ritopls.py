from collections import deque
from datetime import datetime, timedelta
import requests

OCEANIA = 'oce'

platformIds = {OCEANIA: 'OC1', }


class RateLimiter:
    def __init__(self, request_limit, timespan):
        self.request_limit = request_limit
        self.timespan = timespan
        self.reqs = deque()

    def __update(self):
        t = datetime.now()
        while len(self.reqs) > 0 and self.reqs[0] < t:
            self.reqs.popleft()

    def make_req(self):
        self.reqs.append(datetime.now() +
                         timedelta(seconds=self.timespan))

    def available(self):
        self.__update()
        return len(self.reqs) < self.request_limit

    def when_available(self):
        self.__update()
        if self.available:
            return datetime.now()
        else:
            return self.reqs[0]


class LoLException(Exception):
    def __init__(self, error, response):
        self.error = error
        self.headers = response.headers
        self.status_code = response.status_code

    def __str__(self):
        return self.error


class RitoPls:
    def __init__(self, region, api_key, rate_limiters):
        self.region = region
        self.api = api_key
        self.rl = []
        for (rl, timespan) in rate_limiters:
            self.rl.append(RateLimiter(rl, timespan))

    def inc_requests(self):
        for rl in self.rl:
            rl.make_req()

    def available(self):
        for rl in self.rl:
            if not rl.available():
                return False
        return True

    def wait_time_seconds(self):
        when = datetime.now()
        for rl in self.rl:
            rl_when = rl.when_available()
            if rl_when > rl:
                when = rl_when
        return (when - datetime.now()).total_seconds()

    def __check_exceptions(self, request):
        if request.status_code == 400:
            raise LoLException("400: Bad request", request)
        elif request.status_code == 401:
            raise LoLException("401: Unauthorised", request)
        elif request.status_code == 404:
            raise LoLException("404: Game data not found", request)
        elif request.status_code == 429:
            raise LoLException("429: Too many requests", request)
        elif request.status_code == 500:
            raise LoLException("500: Internal server error", request)
        elif request.status_code == 503:
            raise LoLException("503: Service unavailable", request)
        else:
            request.raise_for_status()

    def request(self, endpnt, static=False, **kwargs):
        args = {'api_key': self.api}
        for kw in kwargs:
            if kwargs[kw] is not None:
                args[kw] = kwargs[kw]
        r = requests.get(
            'https://{loc}.api.pvp.net/api/lol/{sdata}{region}/{endpnt}'.format(
                loc=self.region if not static else 'global',
                sdata='' if not static else 'static-data/',
                region=self.region,
                endpnt=endpnt),
            params=args)

        if not static:
            self.inc_requests()

        self.__check_exceptions(r)

        return r.json()

    def observer_request(self, endpnt, **kwargs):
        args = {'api_key': self.api}
        for kw in kwargs:
            if kwargs[kw] is not None:
                args[kw] = kwargs[kw]
        r = requests.get(
            'https://{loc}.api.pvp.net/observer-mode/rest/{endpnt}'.format(
                loc=self.region,
                endpnt=endpnt),
            params=args)

        self.inc_requests()

        self.__check_exceptions(r)

        return r.json()

    def summoners_byname(self, names):
        v = '1.4'
        try:
            return self.request(
                'v{version}/summoner/by-name/{sum_names}'.format(
                    version=v,
                    sum_names=','.join(
                        [n.replace(' ', '').lower() for n in names]
                    )
                )
            )
        except LoLException:
            raise

    def summoner_byname(self, name):
        try:
            return self.summoners_byname([name, ])
        except LoLException:
            raise

    def currentgame(self, summonerId):
        # based on current-game-v1.0
        try:
            return self.observer_request(
                'consumer/getSpectatorGameInfo/{platId}/{sumId}'.format(
                    platId=platformIds[self.region],
                    sumId=summonerId
                )
            )
        except LoLException:
            raise
