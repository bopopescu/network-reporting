from interaction_tests.core import InteractionTestCase

class AccountInteractionTestCase(InteractionTestCase):
    """
    Selenium tests for the account and registration apps, as
    well as for the sign up process.
    """
    # REFACTOR use the shortcuts
    def testRegisterAccount(self):
        """
        Tests the creation of a new account (uses random variables).
        Doesn't test the whole sign up process, just the actual
        registration part.
        """
        # go to register new account
        self.logout()
        self.get('/account/login/')
        register_link = self.browser.find_element_by_id("register-account")
        register_link.click()

        # fill out required fields on registration page
        email_field = self.browser.find_element_by_id("id_email")
        password_field = self.browser.find_element_by_id("id_password1")
        password_again_field = self.browser.find_element_by_id("id_password2")
        first_name_field = self.browser.find_element_by_id("id_first_name")
        last_name_field = self.browser.find_element_by_id("id_last_name")
        company_field = self.browser.find_element_by_id("id_company")
        tos_button = self.browser.find_element_by_id("id_tos")

        test_email = "test" + str(random.randint(1,100)) + "@example.mopub.com"
        email_field.send_keys(test_email)
        password_field.send_keys("test")
        password_again_field.send_keys("test")
        first_name_field.send_keys("Test")
        last_name_field.send_keys("Tester")
        company_field.send_keys("Selenium Test")
        tos_button.click()

        continue_button = self.browser.find_element_by_id("accountForm-submit")
        continue_button.click()

        # find the title and make sure we're in the right place
        page_h1 = self.browser.find_element_by_xpath("//div[@id='titlebar']//h1")
        self.assertTrue(page_h1.text.find("Step 1") > -1)

    # REFACTOR use the shortcuts
    def testSignUpProcess(self):
        """
        Goes through the entire sign up process (registration, create an app,
        create an adunit, code integration, dashboard).
        """
        self.testRegisterAccount()

        app_name_field = self.browser.find_element_by_id("appForm-name")
        app_name_field.send_keys("Robot Unicorn Attack")

        primary_category = self.browser.find_element_by_id('id_primary_category')
        primary_category.click()

        primary_category = self.browser.find_element_by_id('id_primary_category')
        primary_category.click()

        games_option = self.browser.find_element_by_xpath("//option[@value='games']")
        games_option.click()

        adunit_name_field = self.browser.find_element_by_id("appForm-adUnitName")
        adunit_name_field.send_keys('Test Adunit')

        continue_button = self.browser.find_element_by_id("appForm-submit")
        continue_button.click()

        # find the title and make sure we're in the right place
        page_h1 = self.browser.find_element_by_xpath("//div[@id='titlebar']//h1")
        self.assertTrue(page_h1.text.find("Step 2") > -1)

        integration_button = self.browser.find_element_by_id("integration-continue")
        integration_button.click()

        dashboard_h1 = self.browser.find_element_by_xpath("//div[@id='titlebar']//h1")
        self.assertTrue(dashboard_h1.text.find("Dashboard") > -1)

