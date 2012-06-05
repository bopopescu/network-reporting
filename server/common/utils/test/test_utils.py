import os
import sys

sys.path.append(os.environ['PWD'])

from datetime import timedelta

from google.appengine.ext import db
from nose.tools import eq_, ok_, make_decorator

from account.models import Account, User, NetworkConfig
from advertiser.models import Campaign, AdGroup, Creative
from publisher.models import App, AdUnit
from reporting.models import StatsModel
from ad_network_reports.models import AdNetworkLoginCredentials, \
        AdNetworkAppMapper

MODELS = [Account, User, NetworkConfig, App, AdUnit,
          Campaign, AdGroup, Creative, StatsModel,
          AdNetworkLoginCredentials, AdNetworkAppMapper]

ADDED_1 = {'added': 1}
DELETED_1 = {'deleted': 1}
EDITED_1 = {'edited': 1}
UNMODIFIED = {}


def prepend_list(e, li):
    li.insert(0, e)
    return li


def add_lists(list_of_lists):
    result = list_of_lists[0]
    for li in list_of_lists[1:]:
        result = map(sum, zip(result, li))
    return result


def clear_datastore():
    """
    Deletes all objects from the database
    """
    for Model in MODELS:
        db.delete(Model.all())


def debug_key_name(key_name, id_dict):
    return ':'.join([id_dict.get(id, id) for id in key_name.split(':')])


def debug_helper(readable_key_name, expected_counts, actual_counts):
    if expected_counts != actual_counts:
        print
        print readable_key_name
        print 'expected:', expected_counts
        print 'actual:', actual_counts


def dict_eq(dict1, dict2, exclude=[]):
    dict1_keys = set(dict1.keys()) - set(exclude)
    dict2_keys = set(dict2.keys()) - set(exclude)

    msg = "passed dictionary keys did not match: %s %s" % (
            dict1_keys - dict2_keys, dict2_keys - dict1_keys)
    eq_(dict1_keys, dict2_keys, msg)

    for key in dict1_keys:
        value1 = dict1[key]
        value2 = dict2[key]

        if isinstance(value1, db.Model):
            model_key_eq(value1, value2)
        elif isinstance(value1, dict):
            dict_eq(value1, value2)
        elif isinstance(value1, list):
            list_eq(value1, value2)
        else:
            msg = "%s != %s for key %s" % (value1, value2, key)
            eq_(value1, value2, msg)


def list_eq(list1, list2):
    msg = "passed lists have unequal lengths: %s %s" % (
            len(list1), len(list2))
    eq_(len(list1), len(list2), msg)

    for item1, item2 in zip(list1, list2):
        if isinstance(item1, db.Model):
            model_key_eq(item1, item2)
        elif isinstance(item1, dict):
            dict_eq(item1, item2)
        elif isinstance(item1, list):
            list_eq(item1, item2)
        else:
            eq_(item1, item2)


def model_key_eq(model1, model2):
    eq_(model1.key(), model2.key(),
        'Primary key %s does not equal %s' % (model1.key(), model2.key()))


def model_eq(model1, model2, exclude=None, check_primary_key=True):
    """Checks the two input models are equal based on their properties.

    Args:
        model1: A database model
        mode12: A database model
        exclude: A list of model properties to exclude from the
                 equality check
        check_primary_key: Indicates to the method to verify that the
                           key of the objects are equal.
                           NOTE: This is important to ensure that a db
                           objects has been modified not just deleted, copied
                           then created. (default True)

    Raises:
        AssertionError if the models are not equal

    Author:
        Nafis (5/21/2012)
    """

    # many models have unimportant 't' property, also the last login is not
    # particular useful
    exclude = exclude or ['t', 'last_login']
    model1_dict = model_to_dict(model1, exclude, reference_only=True)
    model2_dict = model_to_dict(model2, exclude, reference_only=True)

    # only check that the keys are equal if both objects are in db
    if check_primary_key:
        model_key_eq(model1, model2)
    dict_eq(model1_dict, model2_dict)


def model_to_dict(model, exclude=[], reference_only=False,
        include_references=True):
    model_dict = {}

    for key in model.properties().iterkeys():
        if key in exclude:
            continue
        # by prepending the attribute with '_'
        # we the value of this field as stored in the db
        # in particular, for reference properties this will
        # not dereference, but will only get the foreign key
        if reference_only and not key.startswith('_'):
            key = '_' + key
        value = getattr(model, key)
        if include_references or not isinstance(value, db.Model):
            model_dict[key] = value

    return model_dict


def time_almost_eq(time1, time2, delta=None):
    if not delta:
        delta = timedelta(minutes=1)
    ok_(time1 < time2 + delta and time1 > time2 - delta)


def generate_instance_key(instance):
    if not isinstance(instance, dict):
        instance_dict = model_to_dict(instance, include_references=False)

    return tuple([attr for atrr in key, value for key, value in
        instance_dict.iteritems()])

def reference_properties(instance_dict):
    properties = class_.properties()

    return [(value.__class__, value) for key, value in
            instance_dict.iteritems() if isinstance(value, db.Model)]

def confirm_reference_properties(instance_dict,
                                 instances_for_model_dict,
                                 class_,
                                 index):
    messages = []  # compiles all the failures
    error = False

    keys_set = set([instance.key() for instance in
        instance_dict[key]])
    filtered_instances = instance_dict[key]
    for reference_class, value in reference_properties(
            instance_dict):
        if isinstance(value, str):
            filtered_instances = [instance for instance in
                    filtered_instances if str(instance.key()) ==
                    value]
            key_set = set([instance.key() for instance in
                    filtered_instances])
        else:
            # reference property must be an int
            reference_key = generate_instance_key(
                    added[reference_class][value])
            potential_instances = instances_for_model_dict[
                    reference_class][reference_key]
            key_set = set([instance.key() for instance in
                potential_instances]).intersection(key_set)
            filtered_instances = [instance for instance in
                    filtered_instances if filtered_instances if
                    instance.key() in key_set]
    if not key_set or not filtered_instances:
        messages.append("%s at index %d wasn't created" %
                (class_.__name__, index))
        error = True
    elif len(key_set) != len(filtered_instances):
        raise AssertionError("Confirming %s reference properties at %d "
                "is fucked" % (class_.name, index))

    return messages, error


def get_arg_name(key):
    class_name_translation = {'AdNetworkLoginCredentials':
                                'adnetwork_login_credentials',
                              'AdNetworkAppMapper':
                                'adnetwork_app_mapper'}

    class_name = db.get(key).__class__.__name__
    arg_name = class_name_translation.get(class_name,
            class_name.lower())
    if 'creative' in arg_name:
        arg_name = 'creative'

    return arg_name


def confirm_db(modified=None,
               account=UNMODIFIED,
               user=UNMODIFIED,
               network_config=UNMODIFIED,
               app=UNMODIFIED,
               adunit=UNMODIFIED,
               campaign=UNMODIFIED,
               adgroup=UNMODIFIED,
               creative=UNMODIFIED,
               adnetwork_login_credentials=UNMODIFIED,
               adnetwork_app_mapper=UNMODIFIED):
    """Decorator that confirms that the rest of the db is unchanged

    Args:
        modified: list of Models (one of above `MODELS`) that
                  this decorator is NOT responsible for verifying

    Returns:
        decorator for a method

    Author:
        Nafis Jamal (5/21/2012), (5/30/2012)
        Tiago Bandeira (5/25/2012)
    """

    def _outer(method):
        # this `make_decorator` is necessary so that nose finds the test
        # and has the appropriate doc string
        @make_decorator(method)
        def _wrapped_method(self, *args, **kwargs):
            """Method that wraps a test method and ensures
            that the overall db state has not changed
            except the purposefully modified models.
            """
            # creates dictionary of dictionaries: `Model` -> key -> instance
            # for all db Models before the test has been run
            pre_test_instances_dict = _db_to_dict(MODELS)

            # run the intended test
            method(self, *args, **kwargs)

            # grab db state after the test (similar to before)
            post_test_instances_dict = _db_to_dict(MODELS)

            # confirm that db stats is as intended
            # raises assertion error if one or more models
            # changed unexpectedly
            messages = []  # compiles all the failures
            error = False

            for (model_change_dict, Model) in [(account, Account),
                                            (user, User),
                                            (network_config, NetworkConfig),
                                            (app, App),
                                            (adunit, AdUnit),
                                            (campaign, Campaign),
                                            (adgroup, AdGroup),
                                            (creative, Creative),
                                            (adnetwork_login_credentials, AdNetworkLoginCredentials),
                                            (adnetwork_app_mapper, AdNetworkAppMapper)]:
                print Model.__name__
                expected_additions = model_change_dict.get('added', 0)
                expected_edits = model_change_dict.get('edited', 0)
                expected_deletes = model_change_dict.get('deleted', 0)

                expected_delta = expected_additions - expected_deletes

                # makes sure that the number of objects in the db are as expected
                # according to edits, creates and deletes
                if len(post_test_instances_dict[Model]) != len(pre_test_instances_dict[Model]) + expected_delta:
                    messages.append('%s has %s new models instead of the expected %s' %
                                     (Model.__name__,
                                     len(post_test_instances_dict[Model]) - len(pre_test_instances_dict[Model]),
                                     expected_additions)
                                    )
                    print pre_test_instances_dict[Model], post_test_instances_dict[Model]
                    error = True

                num_edited = 0
                num_deleted = 0
                for key, pre_obj in pre_test_instances_dict[Model].iteritems():
                    if not key in post_test_instances_dict[Model]:
                        num_deleted += 1
                        continue

                    post_obj = post_test_instances_dict[Model][key]
                    try:
                        model_eq(pre_obj, post_obj)
                    except AssertionError:
                        num_edited += 1

                if num_edited != expected_edits:
                    messages.append('Expected %s %ss to be modified, found %s' %
                                     (expected_edits, Model.__name__, num_edited))
                    error = True

                if num_deleted != expected_deletes:
                    messages.append('Expected %s %ss to be deleted, found %s' %
                                     (expected_deletes, Model.__name__, num_deleted))
                    error = True

            # raises an assertion error if any of the model tests failed
            ok_(not error, ', '.join(messages))
        return _wrapped_method
    return _outer


def _db_to_dict(models):
    """
    Pulls the database contents into memory as a dictionary


    Args:
        modified: list of Models

    Returns:
        dictionary, e.g.
        {
         'App': {
                 'key1': obj1,
                 'key2': obj2,
                 ...
                }
        ...
         'Campaign': {
                 'key1': obj1,
                 'key2': obj2,
                 ...
                }
        }
    """
    instances_dict = {}
    for Model in models:
        instances_of_model_dict = {}
        for instance in Model.all().order('__key__'):
            instances_of_model_dict[instance.key()] = instance

        instances_dict[Model] = instances_of_model_dict
    return instances_dict
