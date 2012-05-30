"""
This allows you to do a deep-get of a Model object from Google App Engine datastore.
Deep-get means that any references to other Model objects are followed and those objects are fetched as well, recursively.
The goal is that the returned object is fully local in memory, with no unfetched references, and the object can be pickled.

Created by Simon Radford on Nov 4, 2011.
"""

# TODO: Consider open-sourcing this.

# This could be improved and extended further. For example, we could:
#   Fetch back-references (execute the query and turn it into a list of Model instances)
#   Fetch db.Key and db.ListProperty(db.Key) properties, the same way we do ReferenceProperties

import logging

from google.appengine.ext import db

CONFIG = db.create_config(deadline=2)

def deep_get_from_db(root_keys_or_models, other_models = (), prune = None):
    """
    Deep-get a set of Model instances from the App Engine datastore.
    Deep-get means that any references are fetched recursively, resulting in a fully local object.

    Arguments:
        root_keys_or_models: An iterable of either db keys or Model instances. This is the root set of objects to be fetched.
        other_models: (optional) An iterable of Model instances that we already have.
                This can speed things up because we don't have to go to the datastore for these objects.
        prune: (optional) A function that returns True iff the specified reference should NOT be fetched.
                prune(referring_model_instance, ref_property_name) -> True/False.
                You can use this to avoid pulling down massive amounts of connected objects.
    Return value: A list of the Model instances corresponding to root_keys_or_models, with their references fetched.
    """

    fetched_by_key = {}  # Map: key -> Model instance
    keys_to_fetch = set()
    other_models_by_key = dict((model.key(), model) for model in other_models)

    root_keys = []

    def add_key(key):
        if key is None:
            return
        if key in fetched_by_key:
            return
        if key in other_models_by_key:
            add_model(other_models_by_key[key])
            return
        keys_to_fetch.add(key)

    def add_model(model):
        keys_to_fetch.discard(model.key())
        if model.key() in fetched_by_key:
            return
        fetched_by_key[model.key()] = model
        # For each ReferenceProperty, call add_key() on it
        for ref_prop_name in get_all_reference_properties(model.__class__):
            ref_property = getattr(model.__class__, ref_prop_name)
            ref_key = ref_property.get_value_for_datastore(model) # The key that the model's reference property points to
            pruned = bool(prune and prune(model, ref_prop_name))
            if ref_prop_already_resolved(model, ref_property):
                referenced_model = getattr(model, ref_prop_name)
                if pruned:
                    add_model_without_fetching_children(referenced_model)
                else:
                    add_model(referenced_model)
            elif not pruned:
                add_key(ref_key)

    def add_model_without_fetching_children(model):
        # In general, we add to other_models_by_key instead of fetched_by_key.
        # fetched_by_key is only for models whose children have been fetched.
        if model.key() in fetched_by_key:
            return
        if model.key() in keys_to_fetch:
            add_model(model)
            return
        other_models_by_key[model.key()] = model

    # Handle the root keys / models
    for key_or_model in root_keys_or_models:
        if isinstance(key_or_model, db.Model):
            add_model(key_or_model)
            key = key_or_model.key()
        else:
            add_key(key_or_model)
            key = key_or_model
        root_keys.append(key)

    # Fetch everything
    while keys_to_fetch:
        # Batch-get all the Model instances that we know we need
        models = db.get(list(keys_to_fetch), config=CONFIG)
        for key, model in zip(keys_to_fetch, models):
            if model:
                add_model(model)
            else:
                keys_to_fetch.discard(key)

    # Connect everything and return the result
    log_unfetched = set()
    for model in fetched_by_key.itervalues():
        for ref_prop_name in get_all_reference_properties(model.__class__):
            key = getattr(model.__class__, ref_prop_name).get_value_for_datastore(model)  # The key that the model's reference property points to
            if key is not None:
                if key in fetched_by_key:
                    setattr(model, ref_prop_name, fetched_by_key[key])
                elif key in other_models_by_key:
                    setattr(model, ref_prop_name, other_models_by_key[key])
                else:
                    # Key was not fetched
                    log_unfetched.add(ref_prop_name)
    if log_unfetched:
        log_level = logging.DEBUG if prune else logging.WARNING
        logging.log(log_level, "deep_get_from_db(): Some ref properties were not fetched: %s", tuple(log_unfetched))
    return [fetched_by_key[key] for key in root_keys]


# Helper functions:

def get_all_reference_properties(model_class):
    """
    Returns a list of the names of all the db.ReferenceProperty attributes of the provided class (and its base classes).
    """
    return [name for name in dir(model_class) if isinstance(getattr(model_class, name), db.ReferenceProperty)]

def ref_prop_already_resolved(model_instance, ref_property):
    """
    Returns True iff the specified db.ReferenceProperty has already been resolved / dereferenced / fetched on the specified Model instance.
    Uses a hack into the implementation of db.ReferenceProperty, but it should be ok since we are just asking if it is resolved or not for performance reasons.
    If in doubt, returns False.
    """
    try:
        return getattr(model_instance, '_RESOLVED' + ref_property._attr_name(), None) is not None
    except:
        logging.warning("GAE ReferenceProperty implementation changed! Update ref_prop_already_resolved().")
        return False
