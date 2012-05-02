import logging
import pickle

from google.appengine.api import memcache
from google.appengine.ext import db
from google.appengine.datastore import entity_pb

from common.utils.decorators import wraps_first_arg
from common.utils import simplejson


NAMESPACE = None
#MAX_CACHE_TIME = 60*5 # 5 minutes
MAX_CACHE_TIME = 0 # No expiration

class QueryManager(object):
    """ We use a simplified QueryManager to handle gets and puts """
    Model = None
    
    @classmethod
    def get(cls, keys):
        """ Get based on key name """
        if cls.Model:
            return cls.Model.get(keys)    
        else:
            return db.get(keys)
    
    @classmethod
    @wraps_first_arg
    def put(cls, objs):
        # Otherwise it is a list
        return db.put(objs)
            
    @classmethod
    @wraps_first_arg
    def delete(cls, objs):
        """ Set a property to deleted rather than actually deleting from the db """
        for obj in objs:
            obj.deleted = True
        return cls.put(objs)
        
        
class CachedQueryManager(QueryManager):
    """ Intelligently uses the datastore for speed """
    Model = None

    MEMCACHE_EXPIRY_ONE_DAY = 60 * 60 * 24
    FETCH_LIMIT = 1000
    CHUNK_SIZE = 950000
    MAX_NUMBER_OF_CHUNKS = 32

    @classmethod
    def cache_get_or_insert(cls,keys):
        """ This is currently not used due to cache limitations on appengine.
        However, this can serve as a framework for a standardized cache"""
        if isinstance(keys,str) or isinstance(keys,unicode):
            keys = [keys]
        
        data_dict = memcache.get_multi([k for k in keys],namespace=NAMESPACE)
        logging.info("data dict: %s"%data_dict)
        new_cache_dict = {}
        new_data = False
        for key in keys:
            #strip stupid stuff
            key = key.replace("'", '').replace('"','')
            data = data_dict.get(key,None)
            if not data:
                new_data = True
                logging.info("getting %s from db"%key)
                data = db.get(key)
                new_cache_dict[key] = data
                data_dict[key] = data
            else:
                pass    
        if new_data:        
            memcache.set_multi(new_cache_dict,namespace=NAMESPACE)
        objects = data_dict.values()
        return [obj for obj in objects if not getattr(obj,"deleted",False) ]

    @classmethod
    def cache_put(cls,objs,replace=False):
        """ This is currently not used due to cache limitations on appengine.
        However, this can serve as a framework for a standardized cache"""
        if not isinstance(objs,list):
            objs = [objs]
                
        cache_dict = dict([(str(obj.key()),obj) for obj in objs])
        if replace:
            return memcache.replace_multi(cache_dict,time=MAX_CACHE_TIME,namespace=NAMESPACE) 
        else:    
            return memcache.set_multi(cache_dict,time=MAX_CACHE_TIME,namespace=NAMESPACE)

    @classmethod
    def cache_delete(cls,objs):
        """ This is currently not used due to cache limitations on appengine.
        However, this can serve as a framework for a standardized cache"""
        if not isinstance(objs,list):
            objs = [objs]
        
        return memcache.delete_multi([str(obj.key()) for obj in objs],namespace=NAMESPACE)
    
    @classmethod
    def get_entities_for_account(cls, account, entity_class, include_deleted=False,
                                 include_archived=False):
        """
        Looks up all entities of a certain class associated with a certain account. The return value
        is a dictionary mapping entity keys to entities. For example, passing entity_class=AdGroup
        will return a mapping of adgroup keys to adgroups for the given account.

        This method assumes that entity_class is a db.Model subclass, and that it has
        "account" and "deleted" properties.

        IMPORTANT: as a side effect, this method will store the entire dictionary of entities in
        memcache. Additionally, it will store the LIST of entity KEYS in memcache. This helps to
        optimize cases in which part of the entity dictionary becomes evicted from the cache.
        """
        account_key = str(account.key())
        entity_type = entity_class.entity_type()

        # Try getting the dictionary of entities from memcache.
        entities_memcache_key = "%s_acct_%s" % (entity_type, account_key)
        entities = cls.memcache_get_chunked(entities_memcache_key)
        if entities is not None:
            return cls._filtered_entities(entities, include_deleted, include_archived)

        # The dictionary wasn't in memcache. Check if the list of entity keys is in memcache. If it
        # is, we can avoid doing a query.
        entity_key_list_memcache_key = "%s_keys_acct_%s" % (entity_type, account_key)
        entity_key_list = memcache.get(entity_key_list_memcache_key)
        if entity_key_list is None:
            query = entity_class.all(keys_only=True).filter("account = ", account)
            entity_key_list = query.fetch(cls.FETCH_LIMIT)
            memcache.set(entity_key_list_memcache_key, entity_key_list,
                         time=cls.MEMCACHE_EXPIRY_ONE_DAY)

        # Now that we have the keys, perform a batched GET and store the results in memcache.
        entities_list = entity_class.get(entity_key_list)
        entities = dict((str(e.key()), e) for e in entities_list)
        cls.memcache_set_chunked(entities_memcache_key, entities, time=cls.MEMCACHE_EXPIRY_ONE_DAY)
        return cls._filtered_entities(entities, include_deleted, include_archived)

    @classmethod
    def _filtered_entities(cls, entities, include_deleted, include_archived):
        if not include_deleted:
            keys_of_del_entities = [key for key in entities 
                                    if hasattr(entities[key], 'deleted') and entities[key].deleted]
            for key in keys_of_del_entities:
                del entities[key]
        
        if not include_archived:
            keys_of_arc_entities = [key for key in entities
                                    if hasattr(entities[key], 'archived') and entities[key].archived]
            for key in keys_of_arc_entities:
                del entities[key]
        
        return entities

    @classmethod
    def memcache_flush_entities_for_account_keys(cls, account_keys, entity_class):
        """
        Given a collection of accounts and an entity class, this method will flush from memcache any
        information about the entities for those accounts. For example, if this method is called
        with accounts=[A, B] and entity_class=AdGroup, the cached dictionaries of AdGroups for
        accounts A and B will be flushed. "accounts" may be a set, list, or a single object.
        """
        if isinstance(account_keys, set):
            account_keys = list(account_keys)
        if isinstance(account_keys, (basestring, db.Key)):
            account_keys = [account_keys]
        account_keys = [str(account_key) for account_key in account_keys]
        entity_type = entity_class.entity_type()

        # For each account, we need to flush not only the dictionary of entities, but also the list
        # of entity keys. First, we'll construct lists of the memcache keys we want to delete, so
        # that we can perform batch deletes.

        memcache_keys_for_entity_dicts = []
        memcache_keys_for_entity_key_lists = []
        for account_key in account_keys:
            memcache_keys_for_entity_dicts.append("%s_acct_%s" % (entity_type, account_key))
            memcache_keys_for_entity_key_lists.append("%s_keys_acct_%s" % (entity_type, account_key))
        
        # The entity dictionaries are stored as memcache chunks, so we use delete_multi_chunked.
        dict_delete_success = cls.memcache_delete_multi_chunked(memcache_keys_for_entity_dicts)
        list_delete_success = memcache.delete_multi(memcache_keys_for_entity_key_lists)
        return dict_delete_success and list_delete_success

    @classmethod
    def memcache_set_chunked(cls, key_prefix, value, chunksize=CHUNK_SIZE, 
                             time=MEMCACHE_EXPIRY_ONE_DAY):
        """
        Takes the given value and stores it in memcache as ~1 MB chunks. This method provides a
        convenient way to circumvent the 1 MB size limit on memcache values. The keys for the chunks
        will be "<key_prefix>.<chunk number>". This method also stores the number of chunks under
        the key "<key_prefix>.chunks".
        
        Note: due to memcache API restrictions, this will fail if the value provided exceeds 32 MB.
        """
        pickled_value = pickle.dumps(value, 2)
        values = {}
        num_chunks = 0
        for i in xrange(0, len(pickled_value), chunksize):
            num_chunks += 1
            values["%s.%s" % (key_prefix, i // chunksize)] = pickled_value[i : i + chunksize]
        values["%s.chunks" % key_prefix] = num_chunks
        return memcache.set_multi(values, time=time)

    @classmethod
    def memcache_get_chunked(cls, key_prefix):
        """
        Retrieves the value for this key prefix by getting all of its chunks (see the docstring for
        memcache_set_chunked for an explanation of chunking). Returns None if the "number of chunks"
        key is not found, or if any chunk is missing.
        """
        num_chunks = memcache.get("%s.chunks" % key_prefix)
        if num_chunks is None:
            return None

        num_chunks = int(num_chunks)
        values = []

        # We could batch these memcache GETs, but the common case is that there will only be one
        # chunk.
        for i in xrange(0, num_chunks):
            chunk = memcache.get("%s.%s" % (key_prefix, i))
            if chunk is None:
                return None
            values.append(chunk)

        pickled_value = ''.join(values)
        return pickle.loads(pickled_value)

    @classmethod
    def memcache_delete_chunked(cls, key_prefix):
        """
        Deletes all chunk-related memcache keys for this key_prefix.
        """
        keys_to_delete = cls._chunking_keys_for_prefix(key_prefix)
        return memcache.delete_multi(keys_to_delete)

    @classmethod
    def memcache_delete_multi_chunked(cls, key_prefixes):
        """
        Deletes all chunk-related memcache keys for a list of key prefixes.
        """
        keys_to_delete = []
        for prefix in key_prefixes:
            keys_to_delete += cls._chunking_keys_for_prefix(prefix)
        return memcache.delete_multi(keys_to_delete)

    @classmethod
    def _chunking_keys_for_prefix(cls, prefix):
        """
        Returns the chunk-related memcache keys for the given key prefix. These keys include
        the "number of chunks" key ("<prefix>.chunks"), as well as the keys for individual
        chunks (e.g. "<prefix>.0", "<prefix>.1", etc).
        """
        keys = ["%s.chunks" % prefix]

        # We can't know for sure how many chunks are stored for this key prefix, since our "number
        # of chunks" value may have been evicted. However, we know it's less than 32 (since each
        # chunk is ~1 MB, and each memcache operation has a 32 MB limit).
        keys += ["%s.%d" % (prefix, i) for i in xrange(cls.MAX_NUMBER_OF_CHUNKS)]

        return keys
