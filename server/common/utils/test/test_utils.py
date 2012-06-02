import os
import sys
import inspect

sys.path.append(os.environ['PWD'])

from datetime import timedelta
from collections import Counter, defaultdict

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


def model_to_dict(model, exclude=[], reference_only=False):
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
        model_dict[key] = getattr(model, key)

    return model_dict


def time_almost_eq(time1, time2, delta=None):
    if not delta:
        delta = timedelta(minutes=1)
    ok_(time1 < time2 + delta and time1 > time2 - delta)


def confirm_model_changes(added=None,
               deleted=None,
               marked_as_deleted=None,
               edited=None):
    """Verifies that the changes passed in have been made

    Args:
        added: dict of dicts of what's been added (field value only needs to
            be provided if it differs from the default), key -> field -> value

        deleted: list of keys that have been removed from the db

        marked_as_deleted: list of keys where the only change to the instance is
            that deleted has been set to True

        edited: dict of dicts of what's been modified, key -> field -> value

    Returns:
        decorator for a method

    Author:
        Tiago Bandeira (6/1/2012)
    """
    added = added or {}
    deleted = deleted or []
    marked_as_deleted = marked_as_deleted or []
    edited = edited or {}

    def _outer(method):
        # this `make_decorator` is necessary so that nose finds the test
        # and has the appropriate doc string
        @make_decorator(method)
        def _wrapped_method(self, *args, **kwargs):
            """Method that wraps a test method and ensures
            that the changes passed in have occured
            """
            # creates dictionary: key -> instance
            # for all models that have been edited
            models = db.get([key for key in edited.iterkeys()] + [key for key
                in marked_as_deleted])
            pre_test_instances_dict = dict((model.key(), model) for model in
                models)

            # run the intended test
            method(self, *args, **kwargs)

            # confirm that every modification intended occured
            messages = []  # compiles all the failures
            error = False

            # confirm added
            for key, modified_fields in added.iteritems():
                model = db.get(key)
                model_class = model.__class__

                default_fields = {}
                for field, obj in model_class.properties().iteritems():
                    default_fields[field] = obj.default_value()

                # override the defaults for the fields that have been modified
                model_fields = default_fields
                for field, value in modified_fields.iteritmes():
                    model_fields[field] = value

                try:
                    dict_eq(model_fields, model_to_dict(model))
                except AssertionError as exception:
                    messages.append(exception.message)
                    error = True

            # confirm deleted
            models = [model for model in db.get([key for key in deleted]) if
                    model != None]
            if models:
                error = True
                for model in models:
                    messages.append("%s with key: %s should have been deleted"
                            "and wasn't" % (model.__class__.__name__,
                                model.key()))


            # add marked_as_deleted models to edited
            edited = dict(list(edited) + [(key, {'deleted': True}) for key in
                marked_as_deleted])

            # confirm edited
            for key, fields in edited.itervalues():
                pre_test_model = pre_test_instances_dict[key]
                for field, value in fields:
                    setattr(pre_test_model, field, value)

                try:
                    model_eq(db.get(key), pre_test_model)
                except AssertionError as eception:
                    messages.append(exception.message)
                    error = True

            # raises an assertion error if any of the model tests failed
            ok_(not error, ', '.join(messages))
        return _wrapped_method
    return _outer


def confirm_all_models(added=None,
               deleted=None,
               marked_as_deleted=None,
               edited=None):
    """Decorator that confirms the entire state of the db.

    Decorates method with confirm_db and confirm_model_changes.

    Args:
        added: dict of dicts of what's been added (field value only needs to
            be provided if it differs from the default), key -> field -> value

        deleted: list of keys that have been removed from the db

        marked_as_deleted: list of keys where the only change to the instance is
            that deleted has been set to True

        edited: dict of dicts of what's been modified, key -> field -> value

    Author:
        Tiago Bandeira (6/1/2012)
    """
    added = added or {}
    deleted = deleted or []
    marked_as_deleted = marked_as_deleted or []
    edited = edited or {}

    def _outer(method):
        # this `make_decorator` is necessary so that nose finds the test
        # and has the appropriate doc string
        @make_decorator(method)
        def _wrapped_method(self, *args, **kwargs):
            class_name_translation = {'AdNetworkLoginCredentials':
                                        'adnetwork_login_credentials',
                                      'AdNetworkAppMapper':
                                        'adnetwork_app_mapper'}

            confirm_kwargs = defaultdict(Counter)
            for key in added.iterkeys():
                class_name = db.get(key).__class__.__name__
                arg_name = class_name_translation.get(class_name,
                        class_name.lower())
                if 'creative' in arg_name:
                    arg_name = 'creative'
                confirm_kwargs[arg_name]['added'] += 1

            for key in deleted:
                class_name = db.get(key).__class__.__name__
                arg_name = class_name_translation.get(class_name,
                        class_name.lower())
                if 'creative' in arg_name:
                    arg_name = 'creative'
                confirm_kwargs[arg_name]['deleted'] += 1

            for key in (marked_as_deleted + edited.keys()):
                class_name = db.get(key).__class__.__name__
                arg_name = class_name_translation.get(class_name,
                        class_name.lower())
                if 'creative' in arg_name:
                    arg_name = 'creative'
                confirm_kwargs[arg_name]['edited'] += 1

            # run the intended test
            decorator_1 = confirm_db(**confirm_kwargs)
            decorator_2 = confirm_model_changes(added=added,
                                   deleted=deleted,
                                   marked_as_deleted=marked_as_deleted,
                                   edited=edited)
            decorator_1(decorator_2(method))(self, *args, **kwargs)

        return _wrapped_method
    return _outer


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



def decorate_all_test_methods(decorator):
    """
    Decorator that applies a decorator to all methods in a class

    NOTE: This will also wrap nested methods

    Author:
        Haydn (5/21/2012)
    """
    def decorate(cls):
        for method in inspect.getmembers(cls, inspect.ismethod):
            method_name = method[1].__name__
            if 'mptest' in method_name:
                setattr(cls, method_name, decorator(getattr(cls, method_name)))
        return cls
    return decorate
