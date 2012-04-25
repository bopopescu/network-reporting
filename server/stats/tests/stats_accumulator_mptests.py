import os
import sys

sys.path.append(os.environ['PWD'])
import common.utils.test.setup

import datetime

from nose.tools import assert_equals
from stats.stats_accumulator import _log_attempt

def log_attempt_mptest():
    fire_forget_params = dict(id='adunit1', cid='creative1', 
                              udid='udid1' or '', ua='Android OS')
    fake_time = datetime.datetime(2012, 1, 1, 23, 12, 48, 12314)
    log_string = _log_attempt(fire_forget_params, now=fake_time)
    assert_equals(log_string,
            '0.0.0.0 - - [01/Jan/2012:23:12:48 ] '\
            '"GET /m/req?udid=udid1&ua=Android+OS&id=adunit1&cid=creative1 '\
            'HTTP/1.1" 200 10 - "-"')    
