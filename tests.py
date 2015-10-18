import unittest
import time
from ritopls import RateLimiter


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

if __name__ == "__main__":
    unittest.main()
