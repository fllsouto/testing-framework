from unittest import TestCase
import pytest

from app.xtest_case import MyTestCase, XTestCase
from app.xtest_result import XTestResult
from tests.xtest_case_test import XTestCaseTest


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
    suite_name = "xtest_case_unit_testing#test_xtest_template_method"
    result = XTestResult(suite_name)

    test_case_a = MyTestCase("method_a",)
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
    suite_name = "xtest_case_unit_testing#test_xtest_case_test_stubbing"
    expected_result = "4 run, 0 failed, 0 error."
    result = XTestResult(suite_name)

    test = XTestCaseTest('test_result_success_run')
    test.run(result)

    test = XTestCaseTest('test_result_failure_run')
    test.run(result)

    test = XTestCaseTest('test_result_error_run')
    test.run(result)

    test = XTestCaseTest('test_result_multiple_run')
    test.run(result)

    assert expected_result == result.summary()
