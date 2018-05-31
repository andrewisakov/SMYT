import unittest
import ex_01

class TestFailedEX1(unittest.TestCase):
    def setUp(self):
        pass

    def test_1(self):
        self.assertEqual(ex_01.select('esdfd((esdf)(esdf'), 'esdfd')

    def test_2(self):
        self.assertEqual(ex_01.select('(esdf)(esdf'), '(esdf)')


if __name__ == '__main__':
    unittest.main()
