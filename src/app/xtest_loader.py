from app.xtest_suite import XTestSuite


class XTestLoader:

    TEST_METHOD_PREFIX = "test"

    def __init__(self, debug: bool = False):
        self.debug = debug

    def get_test_case_names(self, test_case_class):
        methods = dir(test_case_class)
        test_method_names = []
        for method in methods:
            if method.startswith(self.TEST_METHOD_PREFIX):
                test_method_names.append(method)

        if self.debug:
            print(f"\nlen(test_method_names): {len(test_method_names)}")
            print(f"test_method_names: {test_method_names}\n")

        return test_method_names

    def make_suite(self, test_case_class):
        suite = XTestSuite()
        for test_method_name in self.get_test_case_names(test_case_class):
            test_method = test_case_class(test_method_name)
            suite.add_test(test_method)
        return suite
