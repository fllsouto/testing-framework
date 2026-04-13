import pytest

from app.xtest_case import MyTestCase, XTestCase
from app.xtest_result import XTestResult


def test_xtest_setup_method():
    error_message = "Subclasses must implement this method"
    with pytest.raises(Exception) as exc:
        XTestCase("").setup()
    assert error_message in str(exc.value)


def test_xtest_tear_down_method():
    error_message = "Subclasses must implement this method"
    with pytest.raises(Exception) as exc:
        XTestCase("").tear_down()
    assert error_message in str(exc.value)


def test_xtest_template_method(capsys):
    suite_name = "xtest_case_unit_testing"
    result = XTestResult(suite_name)

    test_case_a = MyTestCase("method_a",)
    test_case_a.run(result)

    captured = capsys.readouterr()
    assert captured.out.splitlines() == ["setup", "method_a", "tear_down"]

    test_case_b = MyTestCase("method_b")
    test_case_b.run(result)

    captured = capsys.readouterr()
    assert captured.out.splitlines() == ["setup", "method_b", "tear_down"]

    test_case_c = MyTestCase("method_c")
    test_case_c.run(result)

    captured = capsys.readouterr()
    assert captured.out.splitlines() == ["setup", "method_c", "tear_down"]
