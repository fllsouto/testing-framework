from app.xtest_result import XTestResult


class XTestCase:

    def __init__(self, test_method_name: str):
        self.test_method_name = test_method_name

    def run(self, result: XTestResult):
        result.test_started()
        self.setup()
        try:
            test_method = getattr(self, self.test_method_name)
            test_method()
        except AssertionError as e:
            result.add_failure(self.test_method_name)
        except Exception as e:
            result.add_error(self.test_method_name)
        self.tear_down()

    def setup(self):
        raise NotImplementedError("Subclasses must implement this method")

    def tear_down(self):
        raise NotImplementedError("Subclasses must implement this method")


class MyTestCase(XTestCase):

    def setup(self):
        print("setup")

    def tear_down(self):
        print("tear_down")

    def method_a(self):
        print("method_a")

    def method_b(self):
        print("method_b")

    def method_c(self):
        print("method_c")
