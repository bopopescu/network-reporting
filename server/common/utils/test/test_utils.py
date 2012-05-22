import os
import sys
import inspect

sys.path.append(os.environ['PWD'])


from google.appengine.ext import db
from nose.tools import eq_, ok_, make_decorator

from account.models import Account, User, NetworkConfig
from advertiser.models import Campaign, AdGroup, Creative
from publisher.models import App, AdUnit
from reporting.models import StatsModel

MODELS = [Account, User, NetworkConfig, App, AdUnit,
          Campaign, AdGroup, Creative, StatsModel]


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
    eq_(len(list1), len(list2))

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
    eq_(model1.key(), model2.key())


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

    exclude = exclude or ['t']  # many models have unimportant 't' property
    model1_dict = model_to_dict(model1, exclude, reference_only=True)
    model2_dict = model_to_dict(model2, exclude, reference_only=True)

    # only check that the keys are equal if both objects are in db
    if check_primary_key:
        eq_(model1.key(), model2.key(),
            'Primary key %s does not equal %s' % (model1.key(), model2.key()))
    dict_eq(model1_dict, model2_dict)


def model_to_dict(model, exclude=[], reference_only=False):
    model_dict = {}

    for key, prop in model.properties().iteritems():
        if key in exclude:
            continue
        # by prepending the attribute with '_'
        # we the value of this field as stored in the db
        # in particular, for reference properties this will
        # not dereference, but will only get the foreign key
        if reference_only:
            key = '_' + key
        model_dict[key] = getattr(model, key)

    return model_dict


def time_almost_eq(time1, time2, delta):
    ok_(time1 < time2 + delta and time1 > time2 - delta)


def confirm_db(modified=None):
    """Decorator that confirms that the rest of the db is unchanged

    Args:
        modified: list of Models (one of above `MODELS`) that
                  this decorator is NOT responsible for verifying

    Returns:
        wrapped method

    NOTE: This only confirms that extra models are not created
          but does not ensure that all of these models have
          not be modified

    Author:
        Nafis (5/21/2012)
    """
    modified = modified or []

    def _outer(method):
        # this `make_decorator` is necessary so that nose finds the test
        # and has the appropriate doc string
        @make_decorator(method)
        def _wrapped_method(self, *args, **kwargs):
            """Method that wraps a test method and ensures
                that the overall db state has not changed
                except the purposefully modified models.
            """

            # creates dictionary: `Model` -> count for all db Models
            pre_test_count_dict = {}
            for Model in MODELS:
                pre_test_count_dict[Model] = Model.all().count()

            # run the intended test
            method(self, *args, **kwargs)

            # confirm that db stats is as intended
            # raises assertion error if one or more models
            # changed in number unexpectedly
            messages = []  # compiles all the failures
            error = False
            for Model in MODELS:
                if Model not in modified:
                    pre_test_count = pre_test_count_dict[Model]

                    model_query = Model.all()
                    post_test_count = model_query.count()
                    post_test_delete_count = model_query.filter('deleted =', True).count()

                    msg = 'Model %s had %s objects but now has %s' % \
                            (Model.__name__, pre_test_count, post_test_count)

                    if pre_test_count != post_test_count:
                        if (post_test_count - pre_test_count) != post_test_delete_count:
                            messages.append(msg)
                            error = True

            # raises an assertion error if any of the model tests failed
            ok_(not error, ', '.join(messages))
        return _wrapped_method
    return _outer


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
