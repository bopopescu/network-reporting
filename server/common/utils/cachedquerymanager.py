import logging

from google.appengine.api import memcache
from google.appengine.ext import db
from google.appengine.datastore import entity_pb

from django.utils import simplejson

NAMESPACE = None
MAX_CACHE_TIME = 60*5 # 5 minutes

class CachedQueryManager(object):
  Model = None
  
  def get_by_key(self,keys):
    return self.Model.get(keys)  
  
  def cache_get(self,keys):
    if isinstance(keys,str) or isinstance(keys,unicode):
      keys = [keys]
    
    data_dict = memcache.get_multi([k for k in keys],namespace=NAMESPACE)
    logging.info("data dict: %s"%data_dict)
    new_cache_dict = {}
    new_data = False
    for key in keys:
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

  def cache_put(self,objs,replace=False):
    if not isinstance(objs,list):
      objs = [objs]
    
    ### JSON encoding ###
    # for obj in objs:
    #   prop_dict = {}
    #   for prop in obj.properties():
    #     prop_dict[prop] = getattr(obj,prop) # obj.prop
    #   obj_string_value = simplejson.dumps(prop_dict, separators=(',',':') # compact encoding      
    cache_dict = dict([(str(obj.key()),obj) for obj in objs])
    if replace:
      return memcache.replace_multi(cache_dict,time=MAX_CACHE_TIME,namespace=NAMESPACE) 
    else:  
      return memcache.set_multi(cache_dict,time=MAX_CACHE_TIME,namespace=NAMESPACE)

  def cache_delete(self,objs):
    if not isinstance(objs,list):
      objs = [objs]
    
    return memcache.delete_multi([str(obj.key()) for obj in objs],namespace=NAMESPACE)
    
  def serialize_entities(self,models):
   if models is None:
     return None
   elif isinstance(models, db.Model):
     # Just one instance
     return db.model_to_protobuf(models).Encode()
   elif isinstance(models,dict):  
     object_dict = {}
     for k,model in models.iteritems():
       object_dict[k] = db.model_to_protobuf(model).Encode()
     return object_dict
   else:
     # A list
     return [db.model_to_protobuf(x).Encode() for x in models]
     
     
  def deserialize_entities(self,data):
    if data is None:
      return None
    elif isinstance(data, str):
    # Just one instance
      return db.model_from_protobuf(entity_pb.EntityProto(data))
    elif isinstance(data,dict):  
      object_dict = {}
      for k,v in data.iteritems():
        object_dict[k] = db.model_from_protobuf(entity_pb.EntityProto(v))
      return object_dict
    else:
      # list
      return [db.model_from_protobuf(entity_pb.EntityProto(x)) for x in data]
      
      