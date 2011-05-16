import logging
from datetime import datetime
from reporting.query_managers import StatsModelQueryManager


#dims:
    # app, adunit, camp, crtv, priority, hour, day, week, month, country, 'targeting'?, 'custom targeting'?
def build_report(report,account):
    logging.warning("\n\n\nTRYING TO BUILD A REPORT AWESOME\n\n\n")
    manager = StatsModelQueryManager(account)
    #d1 = 'App'
    #d2 = 'AdUnit'
    #d3 = 'Campaign'
    data = report.gen_data()
    print "\n\nData for report is:\n%s\n\n\n" % data
    report.complete_at = datetime.now()
    report.put()



