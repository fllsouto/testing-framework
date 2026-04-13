from app.xtest_case import XTestCase
from app.xtest_result import XTestResult
from app.xtest_stub import XTestStub


class XTestCaseTest(XTestCase):

    def set_up(self):
        self.result = XTestResult()

    def tear_down(self):
        ...

    def test_result_success_run(self):
        stub = XTestStub('test_success')
        stub.run(self.result)
        assert self.result.summary() == "1 run, 0 failed, 0 error."

    def test_result_failure_run(self):
        stub = XTestStub('test_failure')
        stub.run(self.result)
        assert self.result.summary() == "1 run, 1 failed, 0 error."

    def test_result_error_run(self):
        stub = XTestStub('test_errpr')
        stub.run(self.result)
        assert self.result.summary() == "1 run, 0 failed, 1 error."

    def test_result_multiple_run(self):
        stub = XTestStub('test_success')
        stub.run(self.result)
        stub = XTestStub('test_failure')
        stub.run(self.result)
        stub = XTestStub('test_error')
        stub.run(self.result)
        assert self.result.summary() == "3 run, 1 failed, 1 error."

