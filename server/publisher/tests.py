import unittest
from selenium import selenium

class BrowserTestCase(unittest.TestCase):
    def setUp(self):
        self.selenium = selenium("localhost",
                                 4444,
                                 "*firefox",
                                 "http://localhost:8000/")
        self.selenium.start()

    def login(self):
        s = self.selenium
        s.open("/account/login/")
        s.type('name=username', "test@example.com")
        s.type('name=password', "test")
        s.click('id=accountForm-submit')

    def logout(self):
        s = self.selenium
        s.click('id=logout-link')

    def testCreateNewAccount(self):
        s = self.selenium
        self.logout()
        s.wait_for_page_to_load(30000)
        s.open('/')
        s.wait_for_page_to_load(30000)
        s.click("id=register-account")


    def testInventoryLoad(self):
        s = self.selenium
        self.login()
        s.wait_for_page_to_load(30000)
        s.open('/inventory')

    def tearDown(self):
        self.selenium.close()


if __name__ == '__main__':
    unittest.main()