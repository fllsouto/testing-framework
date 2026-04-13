from app.xtest_case import XTestCase
from app.xtest_result import XTestResult
from app.xtest_stub import XTestStub
from app.xtest_spy import XTestSpy
from app.xtest_suite import XTestSuite


class XTestSuiteTest(XTestCase):

    def set_up(self): ...

    def tear_down(self): ...

    def test_suite_size(self):
        suite = XTestSuite()
        suite.add_test(XTestStub("test_success"))
        suite.add_test(XTestStub("test_failure"))
        suite.add_test(XTestStub("test_error"))

        assert len(suite.tests) == 3

    def test_suite_success_run(self):
        result = XTestResult()
        suite = XTestSuite()
        suite.add_test(XTestStub("test_success"))

        suite.run(result)

        assert result.summary() == "1 run, 0 failed, 0 error."

    def test_suite_multiple_run(self):
        result = XTestResult()
        suite = XTestSuite()
        suite.add_test(XTestStub("test_success"))
        suite.add_test(XTestStub("test_failure"))
        suite.add_test(XTestStub("test_error"))

        suite.run(result)

        assert result.summary() == "3 run, 1 failed, 1 error."
