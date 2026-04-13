from app.xtest_case import XTestCase


class XTestStub(XTestCase):

    def set_up(self):
        print("XTestStub#set_up implementation")
    
    def tear_down(self):
        print("XTestStub#tear_down implementation")

    def test_success(self):
        assert True

    def test_failure(self):
        assert False

    def test_error(self):
        raise Exception
