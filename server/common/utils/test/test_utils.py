import os
import sys

sys.path.append(os.environ['PWD'])

from datetime import timedelta
from collections import defaultdict

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
    msg = "passed lists have unequal lengths: %s %s\nlist1: %s\nlist2: %s" % (
            len(list1), len(list2), list1, list2)
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


def confirm_model_changes(method,
                          args=None,
                          kwargs=None,
                          deleted=None,
                          marked_as_deleted=None,
                          edited=None,
                          response_code=200,
                          return_values=None):
    """Verifies that the changes passed in have been made

    Args:
        deleted: list of keys that have been removed from the db

        marked_as_deleted: list of keys where the only change to the instance is
            that deleted has been set to True

        edited: dict of dicts of what's been modified, key -> field -> value

    Author:
        Tiago Bandeira (6/1/2012)
    """
    args = args or []
    kwargs = kwargs or {}
    deleted = deleted or []
    marked_as_deleted = marked_as_deleted or []
    edited = edited or {}

    # creates dictionary: key -> instance
    # for all models that have been edited
    models = db.get([key for key in edited.iterkeys()] + [key for key
        in marked_as_deleted])
    pre_test_instances_dict = dict((model.key(), model) for model in
        models)

    # run the intended test
    response = method(*args, **kwargs)
    eq_(response.status_code, response_code)
    # HACK for returning values when called via decorator in confirm_all_models
    return_values.append(response)

    # confirm that every modification intended occured
    messages = []  # compiles all the failures
    error = False

    # confirm deleted
    deleted_messages, error = confirm_deleted(deleted)
    messages += deleted_messages

    # confirm deleted and marked as deleted
    edited_and_marked_as_deleted, error = confirm_edited_and_marked_as_deleted(
            edited, marked_as_deleted, pre_test_instances_dict)
    messages += edited_and_marked_as_deleted

    # raises an assertion error if any of the model tests failed
    ok_(not error, ', '.join(messages))

def confirm_deleted(deleted):
    """Helper function for confirm_model_changes that confirms it's deleted arg

    Author:
        Tiago Bandeira (6/4/2012)
    """
    messages = []  # compiles all the failures
    error = False

    models = [model for model in db.get([key for key in deleted]) if
            model != None]
    if models:
        error = True
        for model in models:
            messages.append("%s with key: %s should have been deleted"
                    " and wasn't" % (model.__class__.__name__,
                        model.key()))

    return messages, error

def confirm_edited_and_marked_as_deleted(edited,
                                         marked_as_deleted,
                                         pre_test_instances_dict):
    """Helper function for confirm_model_changes that confirms it's edited and
    marked_as_deleted args

    Author:
        Tiago Bandeira (6/4/2012)
    """
    EXCLUDE_STR = 'EXCLUDE'
    messages = []  # compiles all the failures
    error = False

    # add marked_as_deleted models to edited
    all_edited = dict(edited.items() + [(key, {'deleted': True}) for
        key in marked_as_deleted])

    # confirm edited
    for key, fields in all_edited.iteritems():
        pre_test_model = pre_test_instances_dict[key]
        exclude = ['t']
        for field, value in fields.iteritems():
            if value == EXCLUDE_STR:
                exclude.append(field)
            else:
                setattr(pre_test_model, field, value)

        instance = db.get(key)
        try:
            model_eq(instance, pre_test_model, exclude=exclude)
        except AssertionError, exception:
            messages.append(exception.message + ". When checking %s instance "
                    "with %s key" % (instance.__class__.__name__,
                        instance.key()))
            error = True

    return messages, error



def confirm_all_models(method,
                       args=None,
                       kwargs=None,
                       added=None,
                       deleted=None,
                       marked_as_deleted=None,
                       edited=None,
                       response_code=200):
    """Decorator that confirms the entire state of the db.

    Decorates method with confirm_db and confirm_model_changes.

    Args:
        added: dict of Model -> number of new instances

        deleted: list of keys that have been removed from the db

        marked_as_deleted: list of keys where the only change to the instance is
            that deleted has been set to True

        edited: dict of dicts of what's been modified, key -> field -> value

    Author:
        Tiago Bandeira (6/1/2012)
    """
    args = args or []
    kwargs = kwargs or {}
    added = added or {}
    deleted = deleted or []
    marked_as_deleted = marked_as_deleted or []
    edited = edited or {}

    confirm_kwargs = defaultdict(lambda: defaultdict(int))
    for key, value in added.iteritems():
        confirm_kwargs[get_arg_name(key)]['added'] += value

    for key in deleted:
        confirm_kwargs[get_arg_name(key)]['deleted'] += 1

    for key in (marked_as_deleted + edited.keys()):
        confirm_kwargs[get_arg_name(key)]['edited'] += 1

    # run the intended test
    return_values = []
    decorator = confirm_db(**confirm_kwargs)
    decorator(confirm_model_changes)(method, args=args,
            kwargs=kwargs, deleted=deleted,
            marked_as_deleted=marked_as_deleted, edited=edited,
            response_code=response_code, return_values=return_values)

    return return_values[0]


def get_arg_name(key):
    class_name_translation = {'AdNetworkLoginCredentials':
                                'adnetwork_login_credentials',
                              'AdNetworkAppMapper':
                                'adnetwork_app_mapper',
                              'NetworkConfig':
                                'network_config'}

    if isinstance(key, db.Key):
        class_name = db.get(key).__class__.__name__
    else:
        class_name = key.__name__

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
                    except AssertionError, exception:
                        print exception.message
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
