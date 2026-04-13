from app.xtest_case import XTestCase
from app.xtest_result import XTestResult
from app.xtest_stub import XTestStub
from app.xtest_spy import XTestSpy
from app.xtest_suite import XTestSuite

from app.xtest_loader import XTestLoader


class XTestLoaderTest(XTestCase):

    def set_up(self): ...
    def tear_down(self): ...

    def test_create_suite(self):
        loader = XTestLoader()
        suite = loader.make_suite(XTestStub)
        assert len(suite.tests) == 3

    def test_create_suite_of_suites(self):
        loader = XTestLoader()
        stub_suite = loader.make_suite(XTestStub)
        spy_suite = loader.make_suite(XTestSpy)

        suite = XTestSuite()
        suite.add_test(stub_suite)
        suite.add_test(spy_suite)

        assert len(suite.tests) == 2

    def test_get_multiple_test_case_names(self):
        expected_case_names = ["test_error", "test_failure", "test_success"]
        loader = XTestLoader()
        case_names = loader.get_test_case_names(XTestStub)
        assert case_names == expected_case_names

    def test_get_no_test_case_names(self):

        class XTestWaka(XTestCase):
            def foobar(self): ...

        loader = XTestLoader()
        case_names = loader.get_test_case_names(XTestWaka)
        assert case_names == []
