import unittest
from tests import basic
from tests.custom_text_test_runner import CustomTextTestRunner


if __name__ == '__main__':
    basic_suite = unittest.TestLoader().loadTestsFromTestCase(
        basic.BasicTests)

    all_tests = unittest.TestSuite([basic_suite])

    runner = CustomTextTestRunner(
        title='dht22_controller unittest report',
        verbosity=2)
    runner.run(all_tests)
