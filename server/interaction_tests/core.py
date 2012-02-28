"""
Interaction tests for the mopub front-end. Interaction tests
use a live browser to test user actions like clicks, entering
and changing data, and navigation.

The tests in this module use selenium (http://seleniumhq.org/)
and assume a running selenium server on localhost. You'll also
have to have firefox installed.
"""

import unittest
import random
from selenium import webdriver

BROWSER = None

class InteractionTestCase(unittest.TestCase):
    """
    Inheritable base class for testing interaction using selenium.
    Connects to a local selenium server instance before running
    any tests. Provides some common utility methods (login, logout,
    others) that are used in most browser tests.
    """

    def setUp(self):
        # make the browser a singleton so we can reuse the same firefox process
        global BROWSER
        if BROWSER == None:
            BROWSER = webdriver.Firefox()
            # wait 10 seconds for each page to load
            BROWSER.implicitly_wait(10)

        self.browser = BROWSER

    def get(self, link):
        """
        Shortcut for navigating to a link on our endpoint.
        """
        # REFACTOR we should put the endpoint in settings
        page = BROWSER.get("http://localhost:8000" + link)
        return page

    def login(self):
        """
        Shortcut for logging in to the page. Will log out the current session first.
        """
        self.logout()
        self.get("/account/login/")
        email_field = BROWSER.find_element_by_name('username')
        email_field.send_keys("test@example.com")
        password_field = BROWSER.find_element_by_name('password')
        password_field.send_keys("test")
        login_button = BROWSER.find_element_by_id("accountForm-submit")
        login_button.click()

    def logout(self):
        """
        Shortcut for logging out of a page. Kind of jankity but usually works.
        """
        # Try to navigate to '/', which could either be the dashboard page
        # or the account login page depending on whether the user is logged
        # in already. If it finds a logout button it'll click it, otherwise
        # the user is probably not logged in anyway.
        self.get('/')
        try:
            logout_button = BROWSER.find_element_by_id("logout-link")
            logout_button.click()
        except:
            pass

    def click(self, id=None, klass=None, xpath=None, name=None):
        """
        Shortcut for clicking on something in the page, identifiable by
        one and only one of: id, class, xpath, name.
        """
        # REFACTOR allow multiple selectors to be passed in
        if id:
            item = BROWSER.find_element_by_id(id)
        elif klass:
            item = BROWSER.find_element_by_class(klass)
        elif xpath:
            item = BROWSER.find_element_by_xpath(xpath)
        elif name:
            item = BROWSER.find_element_by_name(name)
        else:
            raise Exception('please provide one of: id, class, xpath, name')

        item.click()

    def send_keys(self, keys, id=None, klass=None, xpath=None, name=None):
        """
        Shortcut for typing in to something in the page, identifiable by
        one and only one of: id, class, xpath, name.
        """
        if id:
            item = BROWSER.find_element_by_id(id)
        elif klass:
            item = BROWSER.find_element_by_class(klass)
        elif xpath:
            item = BROWSER.find_element_by_xpath(xpath)
        elif name:
            item = BROWSER.find_element_by_name(name)
        else:
            raise Exception('please provide one of: id, class, xpath, name')

        item.send_keys(keys)

    def select_option(self, select_box_id, option_value):
        """
        Shortcut for selecting an option in a select box.
        """
        select_box = BROWSER.find_element_by_id(select_box_id)
        select_box.click()

        option_xpath = "//select[@id='" + select_box_id + "']" + \
                       "//option[@value='" + option_value + "']"
        option = BROWSER.find_element_by_xpath(option_xpath)
        option.click()
