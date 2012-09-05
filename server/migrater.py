from __future__ import with_statement

from appengine_django import InstallAppengineHelperForDjango
InstallAppengineHelperForDjango()

import logging
import traceback
import urllib2

from common.utils import helpers
from google.appengine.api import images, files
from mapreduce import operation as op
# from reporting.models import StatsModel, MPStatsModel
from account.models import Account
from publisher.models import App
def mapper(s):
    # change entity
    props = {}
    for k in StatsModel.properties():
        props[k] = getattr(s,'_%s'%k) # gets underlying data w/ no derefernce

    for k in s.dynamic_properties():
        props[k] = getattr(s,k)

    account = props.get('account',None)
    offline = props.get('offline',False)
    parent_key = None
    parent = s.parent()

    if not account and parent:
        # parent = StatsModel.get(parent.key())
        # if parent:
        account = parent._account

    if account and parent:
        props.update(account=account)
        parent_key = MPStatsModel.get_key(account=account,
                                          offline=offline,
                                          publisher=None,advertiser=None)
    new_stat = MPStatsModel(parent=parent_key,**props)
    yield op.db.Put(new_stat)
    # or yield op.db.Delete(entity)

def deleter(entity):
    yield op.db.Delete(entity)

def blober(entity):
    image_blob = None
    _attribute = None
    if hasattr(entity, 'icon_blob'):
        image_blob = entity.icon_blob if entity.icon_blob else None
        attribute = 'icon_blob'
        entity.icon = None
    elif hasattr(entity, 'image_blob'):
        image_blob = entity.image_blob if entity.image_blob else None
        attribute = 'image_blob'
    if image_blob_key:
        try:
            helpers.helpers.get_url_for_blob(image_blob)
        # if we get an invalidblobkeyerror that means the image still needs to be transfered
        except InvalidBlobKeyError:
            image = urllib2.urlopen('http://38-aws.mopub-inc.appspot.com/files/serve/%s' % image_blob.key())
            setattr(entity, attribute, store_icon(image.read()))
            yield op.db.Put(entity)

def store_icon(icon):
    # add the icon it to the blob store
    fname = files.blobstore.create(mime_type='image/png')
    with files.open(fname, 'a') as f:
        f.write(icon)
    files.finalize(fname)
    return files.blobstore.get_blob_key(fname)

def blob_urler(obj):
    image_blob = None
    if hasattr(obj, 'icon_blob'):
        image_blob = obj.icon_blob if obj.icon_blob else None
    elif hasattr(obj, 'image_blob'):
        image_blob = obj.image_blob if obj.image_blob else None

    if image_blob and not obj.image_serve_url:
        obj.image_serve_url = helpers.get_url_for_blob(image_blob, ssl=False)
        yield op.db.Put(obj)


def creative_pauser(creative):
    if getattr(creative, 'image_blob', None):
        creative.was_active = creative.active
        creative.active = False
        yield op.db.Put(creative)

def creative_activater(creative):
    if getattr(creative, 'image_blob', None):
        creative.active = creative.was_active
        yield op.db.Put(creative)


def network_configer(obj):
    network_config = getattr(obj, 'network_config', None)
    if network_config:
        if isinstance(obj, Account):
            network_config.account = obj.key()  # key only
        else:
            network_config.account = obj._account  # key only
        yield op.db.Put(network_config)


def migrate_geo_targeting(adgroup):
    try:
        if not adgroup.deleted:
            countries = set([geo_predicate[13:] for geo_predicate in adgroup.geo_predicates])

            if '' in countries:
                countries.remove('')

            if '*' in countries:
                countries.remove('*')

            if 'UK' in countries:
                countries.remove('UK')
                countries.add('GB')

            for country in list(countries):
                if country not in ['BD', 'BE', 'BF', 'BG', 'BA', 'BB', 'WF', 'BL', 'BM', 'BN', 'BO', 'BH', 'BI', 'BJ', 'BT', 'JM', 'BV', 'BW', 'WS', 'BQ', 'BR', 'BS', 'JE', 'BY', 'BZ', 'RU', 'RW', 'RS', 'TL', 'RE', 'TM', 'TJ', 'RO', 'TK', 'GW', 'GU', 'GT', 'GS', 'GR', 'GQ', 'GP', 'JP', 'GY', 'GG', 'GF', 'GE', 'GD', 'GB', 'GA', 'SV', 'GN', 'GM', 'GL', 'GI', 'GH', 'OM', 'TN', 'JO', 'HR', 'HT', 'HU', 'HK', 'HN', 'HM', 'VE', 'PR', 'PS', 'PW', 'PT', 'SJ', 'PY', 'IQ', 'PA', 'PF', 'PG', 'PE', 'PK', 'PH', 'PN', 'PL', 'PM', 'ZM', 'EH', 'EE', 'EG', 'ZA', 'EC', 'IT', 'VN', 'SB', 'EU', 'ET', 'SO', 'ZW', 'SA', 'ES', 'ER', 'ME', 'MD', 'MG', 'MF', 'MA', 'MC', 'UZ', 'MM', 'ML', 'MO', 'MN', 'MH', 'US', 'MU', 'MT', 'MW', 'MV', 'MQ', 'MP', 'MS', 'MR', 'IM', 'UG', 'TZ', 'MY', 'MX', 'IL', 'FR', 'IO', 'SH', 'FI', 'FJ', 'FK', 'FM', 'FO', 'NI', 'NL', 'NO', 'NA', 'VU', 'NC', 'NE', 'NF', 'NG', 'NZ', 'NP', 'NR', 'NU', 'CK', 'CI', 'CH', 'CO', 'CN', 'CM', 'CL', 'CC', 'CA', 'CG', 'CF', 'CD', 'CZ', 'CY', 'CX', 'CR', 'CW', 'CV', 'CU', 'SZ', 'SY', 'SX', 'KG', 'KE', 'SR', 'KI', 'KH', 'KN', 'KM', 'ST', 'SK', 'KR', 'SI', 'KP', 'KW', 'SN', 'SM', 'SL', 'SC', 'KZ', 'KY', 'SG', 'SE', 'SD', 'DO', 'DM', 'DJ', 'DK', 'VG', 'DE', 'YE', 'DZ', 'MK', 'UY', 'YT', 'UM', 'LB', 'LC', 'LA', 'TV', 'TW', 'TT', 'TR', 'LK', 'LI', 'LV', 'TO', 'LT', 'LU', 'LR', 'LS', 'TH', 'TF', 'TG', 'TD', 'TC', 'LY', 'VA', 'VC', 'AE', 'AD', 'AG', 'AF', 'AI', 'VI', 'IS', 'IR', 'AM', 'AL', 'AO', 'AQ', 'AP', 'AS', 'AR', 'AU', 'AT', 'AW', 'IN', 'AX', 'AZ', 'IE', 'ID', 'UA', 'QA', 'MZ']:
                    countries.remove(country)
                    # logging.error('Invalid country %s for AdGroup %s' % (country, adgroup.key()))

            cities = []
            if adgroup.cities:
                if len(countries) == 1:
                    for city in adgroup.cities:
                        latlng, state, name, country = city.split(':')
                        if country == list(countries)[0]:
                            lat, lng = latlng.split(',')
                            cities.append("(%s,%s,'%s','%s','%s')" % (lat, lng, name, state, country))
                        else:
                            logging.error('City %s targeted its country not targeted for AdGroup %s' % (city, adgroup.key()))
                else:
                    logging.error('Cities targeted but not exactly one country for AdGroup %s' % adgroup.key())

            if (adgroup.accept_targeted_locations != True or
                set(adgroup.targeted_countries) != countries or
                adgroup.targeted_regions != [] or
                set(adgroup.targeted_cities) != set(cities) or
                adgroup.targeted_zip_codes != [] or
                adgroup.targeted_carriers != []):

                adgroup.accept_targeted_locations = True
                adgroup.targeted_countries = list(countries)
                adgroup.targeted_regions = []
                adgroup.targeted_cities = cities
                adgroup.targeted_zip_codes = []
                adgroup.targeted_carriers = []

                yield op.db.Put(adgroup)

    except Exception:
        logging.error("AdGroup %s: %s" % (adgroup.key().id_or_name(),
                                          traceback.format_exc()))
