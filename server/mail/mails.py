REPORT_FINISHED_SIMPLE = \
"""Your report for %(dim1)s - %(dim2)s - %(dim3)s for dates %(start)s to %(end)s is ready!  You can download your report in .csv format here:

http://app.mopub.com/reports/export/%(report_key)s/
"""

REPORT_FAILED_SIMPLE = \
"""Your report for %(dim1)s - %(dim2)s - %(dim3)s ranging from dates %(start)s to %(end)s has failed.  This could either be due to your account not having any data for the days specified or other transient errors.  Please try again, or if you are receiving multiple failure notices please notify support@mopub.com"""


REPORT_NO_DATA = \
"""Your report for %(dim1)s - %(dim2)s - %(dim3)s ranging from dates %(start)s to %(end)s did not contain any data.  This could either be due to your account not having any data for the days specified or because data has not been loaded into the reporting system.  Please try again, or if you are receiving multiple failure notices please notify support@mopub.com"""
