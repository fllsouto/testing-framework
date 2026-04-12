class XTestCase:

    def __init__(self, test_method_name: str):
        self.test_method_name = test_method_name

    def run(self):
        self.setup()
        test_method = getattr(self, self.test_method_name)
        test_method()
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
