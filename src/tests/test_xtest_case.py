import pytest

from app.xtest_case import MyTestCase, XTestCase


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
    MyTestCase("method_a").run()

    captured = capsys.readouterr()
    assert captured.out.splitlines() == ["setup", "method_a", "tear_down"]

    MyTestCase("method_b").run()

    captured = capsys.readouterr()
    assert captured.out.splitlines() == ["setup", "method_b", "tear_down"]

    MyTestCase("method_c").run()

    captured = capsys.readouterr()
    assert captured.out.splitlines() == ["setup", "method_c", "tear_down"]
