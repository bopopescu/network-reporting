from datetime import datetime

from reports.query_managers import ReportQueryManager
from reports.models import ScheduledReport


MAN = ReportQueryManager()
NOW = datetime.now()


