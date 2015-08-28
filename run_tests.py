import sys
import unittest
from tests import basic
from tests import temperature
from tests import humidity
from tests.custom_text_test_runner import CustomTextTestRunner


def load(testcase):
    return unittest.TestLoader().loadTestsFromTestCase(testcase)


def filter_tests(test_or_suite, test_cases_or_names, include=False):
    if isinstance(test_or_suite, unittest.TestSuite):
        test_or_suite._tests = filter(
            lambda x: filter_tests(x, test_cases_or_names, include),
            test_or_suite._tests)
        return True
    else:
        matched = any(i in str(test_or_suite) for i in test_cases_or_names)
        if include:
            return matched
        else:
            return not matched


def print_tests(test_or_suite):
    """
    Prints all the tests found. The values returned can be used in --include
    and --exclude filters.
    """
    if isinstance(test_or_suite, unittest.TestSuite):
        filter(lambda x: print_tests(x), test_or_suite._tests)
    else:
        print(str(test_or_suite))


def parse_args(args):
    d = {
        'include': [],
        'exclude': [],
        'print_tests': False
    }
    for arg in args:
        inc = '--inc='
        exc = '--exc='
        if inc in arg:
            d['include'].extend(arg.replace(inc, '').split(','))
        elif exc in arg:
            d['exclude'].extend(arg.replace(exc, '').split(','))
        elif '--print_tests' in arg:
            d['print_tests'] = True

    return d


if __name__ == '__main__':
    basic_suite = load(basic.BasicTests)
    temp_suite = load(temperature.TemperatureTests)
    humi_suite = load(humidity.HumidityTests)

    all_tests = unittest.TestSuite([
        basic_suite,
        temp_suite,
        humi_suite
    ])

    opts = parse_args(sys.argv)
    for key, value in opts.items():
        if not isinstance(value, list): continue
        if len(value) == 0: continue
        if 'include' == key:
            filter_tests(all_tests, test_cases_or_names=value, include=True)
        elif 'exclude' == key:
            filter_tests(all_tests, test_cases_or_names=value, include=False)

    if opts['print_tests']:
        print_tests(all_tests)
        sys.exit(0)

    runner = CustomTextTestRunner(
        title='dht22_controller unittest report',
        verbosity=2)
    runner.run(all_tests)
