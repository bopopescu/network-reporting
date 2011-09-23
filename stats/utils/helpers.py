from datetime import datetime
from utils.timezones import Pacific_tzinfo

# TODO: probably dont need both of these functions.
# make more generic

#assuming form YYYY-MM-DD-HH
def get_datetime_from_str(str):
    arr = str.split('-')
    return datetime(year=int(arr[0]),
                    month=int(arr[1]),
                    day=int(arr[2]),
                    hour=int(arr[3]),
                    tzinfo=Pacific_tzinfo())

#assuming form YYYY-MM-DD
def get_date_from_str(str):
    arr = str.split('-')
    return datetime(year=int(arr[0]),
                    month=int(arr[1]),
                    day=int(arr[2]),
                    tzinfo=Pacific_tzinfo())
