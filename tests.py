import unittest
import time
from ritopls import RitoPls, RateLimiter, OCEANIA

# apikey= "<api_key_here>"
apikey = "b3043444-d68e-40a5-b4e7-2279561cd4fa"
ingame = None
notingame = None


class TestRateLimiter(unittest.TestCase):
    def test_at_limit(self):
        # 2 requests per 2 seconds
        rl = RateLimiter(2, 2)
        # Make 2 requests
        rl.make_req()
        rl.make_req()
        self.assertEqual(rl.available(), False)

    def test_over_limit(self):
        # 1 request per 2 seconds
        rl = RateLimiter(1, 2)
        # Make 2 requests
        rl.make_req()
        rl.make_req()
        self.assertEqual(rl.available(), False)

    def test_under_limit(self):
        # 2 requests per 2 seconds
        rl = RateLimiter(2, 2)
        # Make 1 request
        rl.make_req()
        self.assertEqual(rl.available(), True)

    def test_correct_rate(self):
        # 2 requests per 200ms
        rl = RateLimiter(2, 0.2)
        # Make a request
        rl.make_req()
        self.assertEqual(rl.available(), True)
        # Wait 100ms and make another
        time.sleep(0.1)
        rl.make_req()
        self.assertEqual(rl.available(), False)
        # Wait 120ms
        time.sleep(0.12)
        self.assertEqual(rl.available(), True)


class TestRitoPlsRateLimits(unittest.TestCase):
    def setUp(self):
        self.rp = RitoPls(region=OCEANIA, rate_limiters=[(2, 0.1), (3, 0.2)],
                          api_key=apikey)

    def test_rl1(self):
        self.rp.inc_requests()
        self.rp.inc_requests()
        self.assertFalse(self.rp.available())
        time.sleep(0.11)
        self.assertTrue(self.rp.available())

    def test_rl_both(self):
        self.test_rl1()
        self.rp.inc_requests()
        self.assertFalse(self.rp.available())
        time.sleep(0.1)
        self.assertTrue(self.rp.available())


oce = RitoPls(region=OCEANIA, rate_limiters=[(500, 600), (10, 10)],
              api_key=apikey)


class TestRitoPlsEndPoints(unittest.TestCase):
    def setUp(self):
        while (not oce.available()):
            time.sleep(0.01)

    def test_byname(self):
        res = oce.summoner_byname("Strat")
        self.assertEqual(res['strat']['name'], 'Strat')
        self.assertEqual(res['strat']['id'], 401477)

    def test_currentgame(self):
        if ingame is not None:
            response = oce.summoner_byname(ingame)
            info = next(iter(response.values()))
            sumid = info['id']
            self.setUp()
            currentgame = oce.currentgame(sumid)
            self.assertTrue(currentgame['gameLength'] > 0)

if __name__ == "__main__":
    ingame = input("Enter an OCE summoner currently in a game: ")
    response = oce.summoner_byname(ingame)
    sumid = next(iter(response.values()))['id']
    print(oce.currentgame(sumid))
    notingame = input("Enter an OCE summoner currently NOT in a game: ")
    unittest.main()


class TestStaticEndPoints(unittest.TestCase):
    def test_champlist(self):
        res = oce.static_champion_list()
        self.assertEqual(res["1"]["name"], "Annie")
