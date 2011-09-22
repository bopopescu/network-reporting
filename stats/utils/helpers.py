from datetime import datetime
from utils.timezones import Pacific_tzinfo

# TODO: probably dont need both of these functions.
# make more generic

#assuming form MM-DD-YYYY-HH
def get_datetime_from_str(str):
    arr = str.split('-')
    return datetime(year=int(arr[2]),
                    month=int(arr[0]),
                    day=int(arr[1]),
                    hour=int(arr[3]),
                    tzinfo=Pacific_tzinfo())

#assuming form MM-DD-YYYY
def get_date_from_str(str):
    arr = str.split('-')
    return datetime(year=int(arr[2]),
                    month=int(arr[0]),
                    day=int(arr[1]),
                    tzinfo=Pacific_tzinfo())
