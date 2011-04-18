import logging
from datetime import datetime
from reporting.query_managers import StatsModelQueryManager


def build_report(report,account):
    logging.warning("\n\n\nTRYING TO BUILD A REPORT AWESOME\n\n\n")
    manager = StatsModelQueryManager(account)
    d1 = report.d1
    d2 = report.d2
    d3 = report.d3
    start = report.start
    end = report.end
    #d1 = 'App'
    #d2 = 'AdUnit'
    #d3 = 'Campaign'



    report.complete_at = datetime.now()
    report.put()
