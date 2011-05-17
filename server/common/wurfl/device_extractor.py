import pickle
from optparse import OptionParser

from wurfl import devices


DEFAULT_VALUE = 'N/A'
DEVICES_PICKLE_FILE = 'devices.pkl'
device_dict = {}


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
    
    with open(DEVICES_PICKLE_FILE, 'w') as pickle_file:
        pickle.dump(device_dict, pickle_file)


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