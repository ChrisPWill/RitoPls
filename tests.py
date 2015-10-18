import unittest
import time
from ritopls import RitoPls, RateLimiter, OCEANIA

# apikey= "<api_key_here>"


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


if __name__ == "__main__":
    unittest.main()
