from collections import deque
import datetime


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
                         datetime.timedelta(seconds=self.seconds))

    def available(self):
        self.__update()
        return len(self.reqs) < self.request_limit
