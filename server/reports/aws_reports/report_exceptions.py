class ReportException(Exception):
    def __init__(self, message=None):
        self.message = message 

class MRSubmitError(ReportException):
    def __init__(self, reason, message):
        self.reason = reason
        self.message = message

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
