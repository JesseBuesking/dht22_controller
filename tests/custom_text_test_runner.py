"""
A TestRunner for use with the Python unit testing framework. It
generates a custom report to show the result at a glance.
"""

import datetime
import os
import re
import StringIO
import sys
from termcolor import colored
import time
import unittest
from xml.sax import saxutils
from wwtw import *


def get_terminal_size():
    env = os.environ
    def ioctl_GWINSZ(fd):
        try:
            import fcntl, termios, struct, os
            cr = struct.unpack('hh', fcntl.ioctl(fd, termios.TIOCGWINSZ,
        '1234'))
        except:
            return
        return cr
    cr = ioctl_GWINSZ(0) or ioctl_GWINSZ(1) or ioctl_GWINSZ(2)
    if not cr:
        try:
            fd = os.open(os.ctermid(), os.O_RDONLY)
            cr = ioctl_GWINSZ(fd)
            os.close(fd)
        except:
            pass
    if not cr:
        cr = (env.get('LINES', 25), env.get('COLUMNS', 80))

        ### Use get(key[, default]) instead of a try/catch
        #try:
        #    cr = (env['LINES'], env['COLUMNS'])
        #except:
        #    cr = (25, 80)
    return int(cr[1]), int(cr[0])


__version__ = "0.0.1"


# ------------------------------------------------------------------------
# The redirectors below are used to capture output during testing. Output
# sent to sys.stdout and sys.stderr are automatically captured. However
# in some cases sys.stdout is already cached before CustomTextTestRunner is
# invoked (e.g. calling logging.basicConfig). In order to capture those
# output, use the redirectors for the cached stream.
#
# e.g.
#   >>> logging.basicConfig(stream=CustomTextTestRunner.stdout_redirector)
#   >>>

class OutputRedirector(object):
    """ Wrapper to redirect stdout or stderr """
    def __init__(self, fp):
        self.fp = fp

    def write(self, s):
        self.fp.write(s)

    def writelines(self, lines):
        self.fp.writelines(lines)

    def flush(self):
        self.fp.flush()

stdout_redirector = OutputRedirector(sys.stdout)
stderr_redirector = OutputRedirector(sys.stderr)

TestResult = unittest.TestResult

class _TestResult(TestResult):
    # note: _TestResult is a pure representation of results.
    # It lacks the output and reporting ability compares to unittest._TextTestResult.

    def __init__(self, verbosity=1):
        TestResult.__init__(self)
        self.stdout0 = None
        self.stderr0 = None
        self.success_count = 0
        self.failure_count = 0
        self.error_count = 0
        self.verbosity = verbosity

        # result is a list of result in 4 tuple
        # (
        #   result code (0: success; 1: fail; 2: error),
        #   TestCase object,
        #   Test output (byte string),
        #   stack trace,
        # )
        self.result = []


    def startTest(self, test):
        TestResult.startTest(self, test)
        # just one buffer for both stdout and stderr
        self.outputBuffer = StringIO.StringIO()
        stdout_redirector.fp = self.outputBuffer
        stderr_redirector.fp = self.outputBuffer
        self.stdout0 = sys.stdout
        self.stderr0 = sys.stderr
        sys.stdout = stdout_redirector
        sys.stderr = stderr_redirector


    def complete_output(self):
        """
        Disconnect output redirection and return buffer.
        Safe to call multiple times.
        """
        if self.stdout0:
            sys.stdout = self.stdout0
            sys.stderr = self.stderr0
            self.stdout0 = None
            self.stderr0 = None
        return self.outputBuffer.getvalue()


    def stopTest(self, test):
        # Usually one of addSuccess, addError or addFailure would have been called.
        # But there are some path in unittest that would bypass this.
        # We must disconnect stdout in stopTest(), which is guaranteed to be called.
        self.complete_output()


    def addSuccess(self, test):
        self.success_count += 1
        TestResult.addSuccess(self, test)
        output = self.complete_output()
        self.result.append((0, test, output, ''))
        # if self.verbosity > 1:
        #     sys.stderr.write('ok ')
        #     sys.stderr.write(str(test))
        #     sys.stderr.write('\n')
        # else:
        #     sys.stderr.write('.')
        sys.stderr.write('.')

    def addError(self, test, err):
        self.error_count += 1
        TestResult.addError(self, test, err)
        _, _exc_str = self.errors[-1]
        output = self.complete_output()
        self.result.append((2, test, output, _exc_str))
        # if self.verbosity > 1:
        #     sys.stderr.write('E  ')
        #     sys.stderr.write(str(test))
        #     sys.stderr.write('\n')
        # else:
        #     sys.stderr.write('E')
        sys.stderr.write('E')

    def addFailure(self, test, err):
        self.failure_count += 1
        TestResult.addFailure(self, test, err)
        _, _exc_str = self.failures[-1]
        output = self.complete_output()
        self.result.append((1, test, output, _exc_str))
        # if self.verbosity > 1:
        #     sys.stderr.write('F  ')
        #     sys.stderr.write(str(test))
        #     sys.stderr.write('\n')
        # else:
        #     sys.stderr.write('F')
        sys.stderr.write('F')


def conditional_color(value, color, just=5):
    if int(value) > 0:
        return ljust(colored(str(value), color), just)
    else:
        return ljust(str(value), just)


def getperf(value):
    """ parses out the "[PERF 00:00:00.000]" string from the value if it's there """
    perf = re.search(r'\[PERF .*?(\d{2}:\d{2}:\d{2}(\.\d+)?).*?\]', value)
    if perf is None or not hasattr(perf, 'groups'): return None
    if len(perf.groups()) <= 0: return None
    return perf.groups()[0]

def isskipped(value):
    """ parses out the "skipped 'slow'" string from the value if it's there """
    return 'skipped' in value

def getslow(value):
    """ parses out the "skipped 'slow'" string from the value if it's there """
    slow = re.search(r'(skipped \'slow\')', value)
    if slow is None or not hasattr(slow, 'groups'): return None
    if len(slow.groups()) <= 0: return None
    return slow.groups()[0]

def removecolors(value):
    ansi_escape = re.compile(r'\x1b[^m]*m')
    return ansi_escape.sub('', value)

def ljust(value, just=5):
    ansi_escape = re.compile(r'\x1b[^m]*m')
    l = len(ansi_escape.sub('', value))
    return value.ljust((len(value) - l) + just, ' ')


class CustomTextTestRunner(object):

    def __init__(self, stream=sys.stdout, verbosity=1, title=None, description=None):
        self.stream = stream
        self.verbosity = verbosity
        self.title = 'Custom Text Test Report' if title is None else title
        self.description = '' if description is None else description
        self.sw = StopWatch()
        self.sw.start()
        self._STATUSES = {
            0: colored('pass', 'green'),
            1: colored('fail', 'yellow'),
            2: colored('error', 'red')
        }


    def run(self, test):
        "Run the given test case or test suite."
        result = _TestResult(self.verbosity)
        test(result)
        self.sw.stop()
        self.generateReport(test, result)
        return result


    def sortResult(self, result_list):
        # unittest does not seems to run in any particular order.
        # Here at least we want to group them together by class.
        rmap = {}
        classes = []
        for n,t,o,e in result_list:
            cls = t.__class__
            if not rmap.has_key(cls):
                rmap[cls] = []
                classes.append(cls)
            rmap[cls].append((n,t,o,e))
        r = [(cls, rmap[cls]) for cls in classes]
        return r


    def getReportAttributes(self, result):
        """
        Return report attributes as a list of (name, value).
        Override this to add custom attributes.
        """
        status = '{}{}{}{}'.format(
            ljust(str(result.success_count+result.failure_count+result.error_count)),
            conditional_color(result.success_count, 'green'),
            conditional_color(result.failure_count, 'yellow'),
            conditional_color(result.error_count, 'red')
        )
        return [
            ('CustomTextTestRunner', __version__),
            ('Start Time', self.sw._start.strftime('%Y-%m-%dT%H:%M:%S')),
            ('Duration', self.sw.pretty(4)),
            ('Status', status),
        ]


    def generateReport(self, test, result):
        report_attrs = self.getReportAttributes(result)
        heading = self._generate_heading(report_attrs)
        report = self._generate_report(result)
        ending = self._generate_ending()

        output = '\n'

        if heading is not None and heading.strip() != '':
            output += '\n{}'.format(heading)

        if report is not None and report.strip() != '':
            output += '\n{}'.format(report)

        width = get_terminal_size()[0]
        output += '\n' + '~'*width + '\n'
        output += 'Report summary: {}{}{}{}'.format(
            ljust(str(result.success_count+result.failure_count+result.error_count)),
            conditional_color(result.success_count, 'green'),
            conditional_color(result.failure_count, 'yellow'),
            conditional_color(result.error_count, 'red'),
        )

        if ending is not None and ending.strip() != '':
            output += '\n{}'.format(ending)

        output += '\n    Start Time: {}'.format(self.sw._start.strftime('%Y-%m-%dT%H:%M:%S'))
        output += '\n      Duration: {}'.format(self.sw.pretty(4))
        width = get_terminal_size()[0]
        output += '\n' + '~'*width + '\n'
        self.stream.write(output.encode('utf8'))


    def _generate_heading(self, report_attrs):
        a_lines = []
        for name, value in report_attrs:
            line = '{}: {}\n'.format(ljust(str(name), 20), value)
            a_lines.append(line)

        heading = self.title.upper() + ':'
        heading += '\n' + '='*(len(self.title) + 1)
        heading += '\n{}'.format(''.join(a_lines))
        if self.description is not None:
            heading += '\n\n{}'.format(self.description)
        heading = heading.rstrip('\n')
        return heading


    def _generate_report(self, result):
        rows = []

        sortedResult = self.sortResult(result.result)
        for cid, (cls, cls_results) in enumerate(sortedResult):
            # subtotal for a class
            np = nf = ne = 0
            for n, t, o, e in cls_results:
                if n == 0: np += 1
                elif n == 1: nf += 1
                else: ne += 1

            # format class description
            if cls.__module__ == "__main__":
                name = cls.__name__
            else:
                name = "%s.%s" % (cls.__module__, cls.__name__)

            doc = cls.__doc__ and cls.__doc__.split("\n")[0] or ""
            desc = doc and '%s: %s' % (name, doc) or name

            test_name = desc
            num_tests = np + nf + ne
            passed = np
            failed = nf
            errored = ne

            test_summary = '\n{}{}{}{} | {}'.format(
                ljust(colored(str(num_tests), 'white')),
                conditional_color(passed, 'green'),
                conditional_color(failed, 'yellow'),
                conditional_color(errored, 'red'), test_name
            )
            test_summary += "\n"

            row = test_summary
            width = get_terminal_size()[0]
            rows.append('\n' + '-'*width)
            rows.append(row)

            for n, t, o, e in cls_results:
                self._generate_report_test(rows, cid, n, t, o, e)
            # add a newline between test classes
            rows.append('\n')

        report = ''.join(rows)
        return report


    def _generate_report_test(self, rows, cid, n, t, o, e):
        # e.g. 'pt1.1', 'ft1.1', etc
        has_output = bool(o or e)
        name = t.id().split('.')[-1]
        doc = t.shortDescription() or ""
        desc = doc and ('%s: %s' % (name, doc)) or name

        # o and e should be byte string because they are collected from stdout and stderr?
        if isinstance(o, str):
            # TODO: some problem with 'string_escape': it escape \n and mess up formating
            # uo = unicode(o.encode('string_escape'))
            uo = o.decode('latin-1')
        else:
            uo = o
        if isinstance(e, str):
            # TODO: some problem with 'string_escape': it escape \n and mess up formating
            # ue = unicode(e.encode('string_escape'))
            ue = e.decode('latin-1')
        else:
            ue = e

        # super custom depending on our own custom decorators
        #   nutshell: this reads the output that was captured to see if
        #   certain decorators were applied, and if so it customizes the
        #   output for this test runner
        skipped = False
        perf = None
        slow = None
        if uo is not None and uo.strip() != '':
            perf = getperf(uo)
            slow = getslow(uo)
            skipped = isskipped(uo)

        if ue is not None and ue.strip() != '':
            perf = getperf(ue)
            slow = getslow(ue)
            skipped = isskipped(ue)

        row = ljust('  ' + desc, 40)

        def getstatus(n):
            if skipped:
                return colored('skipped', 'grey')
            else:
                return self._STATUSES[n]

        status = '[pass]'
        lstatus = 0
        if slow is not None:
            status = '[{}]'.format(colored('skipped - slow', 'grey'))
        elif perf is not None and not skipped:
            status = '[{}]'.format(colored(perf, 'blue'))
            status += ' [{}]'.format(getstatus(n))
        else:
            lstatus = 2 + len(getstatus(n)) # 2 = []
            status = '[{}]'.format(getstatus(n))

        lstatus = len(removecolors(status))

        width = get_terminal_size()[0]
        # no more than console width
        row = row[:width]
        # at least console width
        if len(row) < width:
            row = row + ' '*(width - len(row))
        # make room for the status
        row = row[:-(lstatus + 1)]
        # add the status
        row += ' ' + status

        width = get_terminal_size()[0]
        if ue is not None and ue.strip() != '':
            error = '\n' + '='*width
            error += '\n    {}'.format(ue.replace('\n', '\n    '))
            error += '\n' + '='*width
            row += colored(error, 'magenta')

        rows.append(row)
        if not has_output:
            return

    def _generate_ending(self):
        return ""


##############################################################################
# Facilities for running tests from the command line
##############################################################################

# Note: Reuse unittest.TestProgram to launch test. In the future we may
# build our own launcher to support more specific command line
# parameters like test title, CSS, etc.
class TestProgram(unittest.TestProgram):
    """
    A variation of the unittest.TestProgram. Please refer to the base
    class for command line parameters.
    """
    def runTests(self):
        # Pick CustomTextTestRunner as the default test runner.
        # base class's testRunner parameter is not useful because it means
        # we have to instantiate CustomTextTestRunner before we know self.verbosity.
        if self.testRunner is None:
            self.testRunner = CustomTextTestRunner(verbosity=self.verbosity)
        unittest.TestProgram.runTests(self)

main = TestProgram

##############################################################################
# Executing this module from the command line
##############################################################################

if __name__ == "__main__":
    main(module=None)
