import pickle

FILES = ('brand_marketing', 'brand_os', 'brand_osversion', 'marketing_os', 'marketing_osversion', 'os_brand', 'os_marketing', 'os_osversion', 'osversion_brand', 'osversion_marketing')

DICTS = []
for file in FILES:
    DICTS.append(pickle.load(file + '_dict.pkl'))

BRAND_MAR, BRAND_OS, BRAND_OSVER, MAR_OS, MAR_OSVER, OS_BRAND, OS_MAR, OS_OSVER, OSVER_BRAND, OSVER_MAR = DICTS




