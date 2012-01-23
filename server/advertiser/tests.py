import unittest

from forms import CampaignForm, AdGroupForm

class TestCampaignForm(unittest.TestCase):

    def setUp(self):
        pass

    def test_gtee_campaign_type(self):
        data = {
            'campaign_type': 'gtee',
            'name': 'Testing Campaign',
        }

        for gtee_priority, campaign_type in (
            ('high', 'gtee_high'),
            ('normal', 'gtee'),
            ('low', 'gtee_low')):
            data['gtee_priority'] = gtee_priority
            form = CampaignForm(data)
            """
            self.assertTrue(form.is_valid())
            campaign = form.save()
            self.assertEqual(campaign.campaign_type, campaign_type)
            """

    def test_form(self):
        valid_data = {'campaign_type': 'gtee',
                      'gtee_priority': 'high'}

        campaign_form = CampaignForm()
        self.assertFalse(campaign_form.is_valid())


if __name__ == '__main__':
    unittest.main()
