from collections import deque
from datetime import datetime, timedelta

OCEANIA = 'oce'


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
