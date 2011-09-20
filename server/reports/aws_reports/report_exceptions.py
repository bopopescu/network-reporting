class ReportException(Exception):
    def __init__(self, key=None):
        self.report_key = key

class MRSubmitError(ReportException):
    def __init__(self, reason, report_key):
        self.reason = reason
        self.report_key = report_key

class NoDataError(MRSubmitError):
    pass

class ReportParseError(ReportException):
    pass

class BlobUploadError(ReportException):
    pass

class S3Error(ReportException):
    pass

class ReportPutError(ReportException):
    pass

class ReportNotifyError(ReportException):
    pass
