from app.xtest_result import XTestResult


class XTestRunner:

    def __init__(self):
        self.result = XTestResult()

    def run(self, test):
        test.run(self.result)
        print(self.result.summary())
        return self.result
