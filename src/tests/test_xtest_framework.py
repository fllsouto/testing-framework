from unittest import TestCase
import pytest

from app.xtest_case import MyTestCase, XTestCase
from app.xtest_result import XTestResult
from tests.xtest_case_test import XTestCaseTest
from tests.xtest_suite_test import XTestSuiteTest
from app.xtest_suite import XTestSuite


def test_xtest_set_up_method():
    error_message = "Subclasses must implement this method"
    with pytest.raises(Exception) as exc:
        XTestCase("").set_up()
    assert error_message in str(exc.value)


def test_xtest_tear_down_method():
    error_message = "Subclasses must implement this method"
    with pytest.raises(Exception) as exc:
        XTestCase("").tear_down()
    assert error_message in str(exc.value)


def test_xtest_template_method(capsys):
    suite_name = "xtest_framework_unit_testing#test_xtest_template_method"
    result = XTestResult(suite_name)

    test_case_a = MyTestCase(
        "method_a",
    )
    test_case_a.run(result)

    captured = capsys.readouterr()
    assert captured.out.splitlines() == ["set_up", "method_a", "tear_down"]

    test_case_b = MyTestCase("method_b")
    test_case_b.run(result)

    captured = capsys.readouterr()
    assert captured.out.splitlines() == ["set_up", "method_b", "tear_down"]

    test_case_c = MyTestCase("method_c")
    test_case_c.run(result)

    captured = capsys.readouterr()
    assert captured.out.splitlines() == ["set_up", "method_c", "tear_down"]


def test_xtest_case_test_stubbing():
    suite_name = "xtest_framework_unit_testing#test_xtest_case_test_stubbing"
    expected_result = "4 run, 0 failed, 0 error."
    result = XTestResult(suite_name)

    test = XTestCaseTest("test_result_success_run")
    test.run(result)

    test = XTestCaseTest("test_result_failure_run")
    test.run(result)

    test = XTestCaseTest("test_result_error_run")
    test.run(result)

    test = XTestCaseTest("test_result_multiple_run")
    test.run(result)

    assert result.summary() == expected_result


def test_xtest_case_test_spying():
    suite_name = "xtest_framework_unit_testing#test_xtest_case_test_spying"
    expected_result = "4 run, 0 failed, 0 error."
    result = XTestResult(suite_name)

    test = XTestCaseTest("test_was_set_up")
    test.run(result)

    test = XTestCaseTest("test_was_run")
    test.run(result)

    test = XTestCaseTest("test_was_tear_down")
    test.run(result)

    test = XTestCaseTest("test_template_method")
    test.run(result)

    assert result.summary() == expected_result


def test_xtest_suite_test_basic():
    suite_name = "xtest_framework_unit_testing#test_xtest_suite_test_basic"
    expected_result = "3 run, 0 failed, 0 error."
    result = XTestResult(suite_name)

    suite = XTestSuiteTest("test_suite_size")
    suite.run(result)

    suite = XTestSuiteTest("test_suite_success_run")
    suite.run(result)

    suite = XTestSuiteTest("test_suite_multiple_run")
    suite.run(result)

    assert result.summary() == expected_result


@pytest.fixture
def complete_suite():
    return [
        XTestCaseTest("test_result_success_run"),
        XTestCaseTest("test_result_failure_run"),
        XTestCaseTest("test_result_error_run"),
        XTestCaseTest("test_result_multiple_run"),
        XTestCaseTest("test_was_set_up"),
        XTestCaseTest("test_was_run"),
        XTestCaseTest("test_was_tear_down"),
        XTestCaseTest("test_template_method"),
        XTestSuiteTest("test_suite_size"),
        XTestSuiteTest("test_suite_success_run"),
        XTestSuiteTest("test_suite_multiple_run"),
    ]


def test_xtest_suite_test_complete(complete_suite):
    suite_name = "xtest_framework_unit_testing#test_xtest_suite_test_complete"
    expected_result = "11 run, 0 failed, 0 error."
    result = XTestResult(suite_name)
    suite = XTestSuite()

    for test in complete_suite:
        suite.add_test(test)

    suite.run(result)

    assert result.summary() == expected_result
