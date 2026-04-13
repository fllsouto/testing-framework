from app.xtest_result import XTestResult


class XTestCase:

    def __init__(self, test_method_name: str):
        self.test_method_name = test_method_name

    def run(self, result: XTestResult):
        result.test_started()
        self.set_up()
        try:
            test_method = getattr(self, self.test_method_name)
            test_method()
        except AssertionError as e:
            print("Error type: AssertionError")
            print(e)
            result.add_failure(self.test_method_name)
        except Exception as e:
            print("Error type: Exception")
            print(e)
            result.add_error(self.test_method_name)
        self.tear_down()

    def set_up(self):
        raise NotImplementedError(
            "Subclasses must implement this method: XTestCase#set_up"
        )

    def tear_down(self):
        raise NotImplementedError(
            "Subclasses must implement this method: XTestCase#tear_down"
        )


class MyTestCase(XTestCase):

    def set_up(self):
        print("set_up")

    def tear_down(self):
        print("tear_down")

    def method_a(self):
        print("method_a")

    def method_b(self):
        print("method_b")

    def method_c(self):
        print("method_c")
