import pickle
from optparse import OptionParser

from wurfl import devices


DEFAULT_VALUE = 'N/A'
DEVICES_PICKLE_FILE = 'devices.pkl'

# dict containing all device info from WURFL
# k: devid
# v: [brand_name, marketing_name, os, os_version]
device_dict = {}


# 10 dicts covering the mapping and reverse-mapping relationships among the properties
# dict name convention: <key>_<list of values>_dict

# bi-directional
brand_marketing_dict = {}
marketing_brand_dict = {}

# bi-directional
os_osversion_dict = {}
osversion_os_dict = {}

# bi-directional
brand_os_dict = {}
os_brand_dict = {}

# bi-directional
marketing_osversion_dict = {}
osversion_marketing_dict = {}

# bi-directional
brand_osversion_dict = {}
osversion_brand_dict = {}

# bi-directional
marketing_os_dict = {}
os_marketing_dict = {}

# list of pairs mapping dict name to dict
dict_list = [('brand_marketing_dict', brand_marketing_dict), ('marketing_brand_dict', marketing_brand_dict),
             ('os_osversion_dict', os_osversion_dict), ('osversion_os_dict', osversion_os_dict),
             ('brand_os_dict', brand_os_dict), ('os_brand_dict', os_brand_dict),
             ('marketing_osversion_dict', marketing_osversion_dict), ('osversion_marketing_dict', osversion_marketing_dict),
             ('brand_osversion_dict', brand_osversion_dict), ('osversion_brand_dict', osversion_brand_dict),
             ('marketing_os_dict', marketing_os_dict), ('os_marketing_dict', os_marketing_dict)]



def main():
    parser = OptionParser()
    parser.add_option('-v', '--verbose', action='store_true', dest='verbose')
    (options, args) = parser.parse_args()
    
    for devid in devices.devids.keys():        
        get_device_info(devid) 
    
    if options.verbose:
        for devid, info in device_dict.iteritems():
            print "%s\t%s" % (devid, info)
    print "%i devices extracted from WURFL file" % (len(device_dict))
    
    create_mappings()
    pickle_dicts()



def pickle_dicts():
    for (name, d) in dict_list:
        print 'pickling %s ...' %(name)
        with open(name+'.pkl', 'w') as pickle_file:
            pickle.dump(d, pickle_file)


def update(d, k, v):
    if k in d:
        d[k].add(v)
    else:
        d[k] = set([v])


def create_mappings():
    # populate mapping and reverse-mapping dicts from device_dict
    for devid, [brand_name, marketing_name, os, os_version] in device_dict.iteritems():
        update(brand_marketing_dict, brand_name, marketing_name)
        update(marketing_brand_dict, marketing_name, brand_name)

        update(os_osversion_dict, os, os_version)
        update(osversion_os_dict, os_version, os)
        
        update(brand_os_dict, brand_name, os)
        update(os_brand_dict, os, brand_name)
        
        update(marketing_osversion_dict, marketing_name, os_version)
        update(osversion_marketing_dict, os_version, marketing_name)

        update(brand_osversion_dict, brand_name, os_version)
        update(osversion_brand_dict, os_version, brand_name)

        update(marketing_os_dict, marketing_name, os)
        update(os_marketing_dict, os, marketing_name)

    # for each dict, convert the value from set to list
    for (name, d) in dict_list:
        print 'converting values from set to list in %s ...' %(name)
        for k, v in d.iteritems():
            d[k] = list(v)


def get_device_info(devid):
    try:
        if devid in device_dict:
            return device_dict[devid]
            
        device = devices.select_id(devid)

        # wurfl data are in unicode
        # convert to str since datastore keynames are str
        # replace spaces with underscores since datastore keynames don't have spaces 
        brand_name = str(device.brand_name.replace(' ', '_') or DEFAULT_VALUE)
        marketing_name = str((device.marketing_name or device.model_name).replace(' ', '_') or DEFAULT_VALUE)
        device_os = str(device.device_os.replace(' ', '_') or DEFAULT_VALUE)
        device_os_version = str(device.device_os_version.replace(' ', '_') or DEFAULT_VALUE)
                
        info = [brand_name, marketing_name, device_os, device_os_version]
        if DEFAULT_VALUE in info:
            info = map(override, info, get_device_info(device.fall_back))
        device_dict[devid] = info
        return info
    except:
        return [DEFAULT_VALUE, DEFAULT_VALUE, DEFAULT_VALUE, DEFAULT_VALUE]
    
    
def override(v1, v2):
    return v1 if v1 != DEFAULT_VALUE else v2

    

if __name__ == '__main__':
    main()
