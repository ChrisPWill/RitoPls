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
        self.realm = None
        self.refresh_realm()

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

        try:
            self.__check_exceptions(r)
        except LoLException:
            raise

        return r.json()

    def static_request(self, endpnt, **kwargs):
        version = '1.2'
        # check if realm needs a refresh
        return self.request(
            'v{version}/{endpnt}'.format(
                version=version,
                endpnt=endpnt
            ),
            static=True,
            **kwargs
        )

    def refresh_realm(self):
        oldrealm = self.realm
        try:
            self.realm = self.static_request(endpnt='realm')
        except:
            self.realm = oldrealm
        else:
            self.last_realm_refresh = datetime.now()

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

        try:
            self.__check_exceptions(r)
        except LoLException:
            raise

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

    def match(self, matchId):
        v = '2.2'
        try:
            return self.request(
                'v{version}/match/{matchId}'.format(version=v, matchId=matchId)
            )
        except LoLException as e:
            if e.status_code is 404:
                return None
            else:
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
        except LoLException as e:
            print (e.status_code)
            if e.status_code is 404:
                return None
            else:
                raise

    def static_champion_list(self, locale='en_US', version=None,
                             data_by_id=False, champ_data='recommended,image'):
        return self.static_request(
            endpnt='champion',
            locale=locale,
            version=version,
            dataById=data_by_id,
            champData=champ_data
        )

    def static_champ_icon_url(self, icon_filename):
        return ("http://ddragon.leagueoflegends.com/cdn/"
                "{dd}/img/champion/{filename}").format(
            dd=str(self.realm['dd']),
            filename=icon_filename
            )

    def static_profile_icon_url(self, icon_id):
        return ("http://ddragon.leagueoflegends.com/cdn/"
                "{dd}/img/profileicon/{iid}.png").format(
            dd=str(self.realm['dd']),
            iid=icon_id
            )
