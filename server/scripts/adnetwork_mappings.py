import os
import sys
import traceback
import codecs
import csv
import json

from optparse import OptionParser

# add mopub root to path relative to this file
sys.path.append("/Applications/GoogleAppEngineLauncher.app/Contents/Resources/GoogleAppEngine-default.bundle/Contents/Resources/google_appengine")
sys.path.append("/Applications/GoogleAppEngineLauncher.app/Contents/Resources/GoogleAppEngine-default.bundle/Contents/Resources/google_appengine/lib/django")
sys.path.append("/Applications/GoogleAppEngineLauncher.app/Contents/Resources/GoogleAppEngine-default.bundle/Contents/Resources/google_appengine/lib/webob")
sys.path.append("/Applications/GoogleAppEngineLauncher.app/Contents/Resources/GoogleAppEngine-default.bundle/Contents/Resources/google_appengine/lib/yaml/lib")
sys.path.append("/Applications/GoogleAppEngineLauncher.app/Contents/Resources/GoogleAppEngine-default.bundle/Contents/Resources/google_appengine/lib/fancy_urllib")
sys.path.append("/Applications/GoogleAppEngineLauncher.app/Contents/Resources/GoogleAppEngine-default.bundle/Contents/Resources/google_appengine/lib/antlr3")
sys.path.append("/Applications/GoogleAppEngineLauncher.app/Contents/Resources/GoogleAppEngine-default.bundle/Contents/Resources/google_appengine/lib/ipaddr")

sys.path.append('/'.join(os.getcwd().split("/")[:-1]))
sys.path.append('.')
CUR_DIR = os.path.dirname(os.path.abspath( __file__ ))
sys.path.append(CUR_DIR+'/..')

from appengine_django import InstallAppengineHelperForDjango
InstallAppengineHelperForDjango()

from common.utils import helpers
from reporting.aws_logging import utils

from advertiser.models import Creative, AdGroup, Campaign
from publisher.models import AdUnit, App, Account

from id_mapper_utils import create_unicode_mapping_file, upload_file_to_S3

def normalize(s):
    import unicodedata
    return unicodedata.normalize('NFKD', unicode(s)).encode('ascii','ignore')

def main():
    # setup remote connection to datastore
    utils.setup_remote_api()

    creatives = helpers.get_all(Creative)
    # adgroups = helpers.get_all(AdGroup, limit=10, testing=True)
    # 
    # adgroup_dict = {}
    # for adgroup in adgroups:
    #     adgroup_dict[str(adgroup.key())] = adgroup
    #
    # for creative in creatives:
    #     creative.adgroup = adgroup_dict[str(creative._adgroup)]

    adunits = helpers.get_all(AdUnit)
    apps = helpers.get_all(App)
    
    app_dict = {}
    for app in apps:
        app_dict[str(app.key())] = app


    for adunit in adunits:
        if adunit._app_key:
            adunit.app = app_dict[str(adunit._app_key)]
        else:
            adunit.app = None

    adunit_mappings = []
    for adunit in adunits:
        adunit_mappings.append([str(adunit.key()),  str(adunit.app.key()) if adunit.app else 'NONE', helpers.to_uni('%s - %s' % (adunit.app.name if adunit.app else 'NONE', adunit.name))])

    creative_mappings = []
    for creative in creatives:
        network_type = getattr(creative, 'network_name', None)
        if network_type:
            creative_mappings.append([str(creative.key()), str(creative._ad_group), str(network_type.lower())])

    f = codecs.open('creative_mappings.txt', encoding='utf-8', mode='w')
    creative_writer = csv.writer(f, delimiter='\t', quotechar='|', quoting=csv.QUOTE_MINIMAL)
    
    for creative_mapping in creative_mappings:
        creative_writer.writerow(creative_mapping)
    f.close()

    f = codecs.open('adunit_mappings.txt', encoding='utf-8', mode='w')
    adunit_writer = csv.writer(f, delimiter='\t', quotechar='|', quoting=csv.QUOTE_MINIMAL)

    for adunit_mapping in adunit_mappings:
        adunit_mapping[2] = normalize(adunit_mapping[2])
        # if 'Unlock' in adunit_mapping[2]:
        #     asdf = json.loads(adunit_mapping[2], encoding='latin-1')['BULLSHIT']
        #     print helpers.to_ascii()
        # print type(adunit_mapping[2]), adunit_mapping[2]
        adunit_writer.writerow(adunit_mapping)

    f.close()


if __name__ == '__main__':
    main()