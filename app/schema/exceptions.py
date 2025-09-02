class AppException(Exception):
    status = 500

    def __init__(self, detail=None, **kwargs):
        self.detail = detail or ""
        self.status = kwargs.get("status") or self.status

        msg = f"({self.status}) {self.detail}"
        super(Exception, self).__init__(msg)

    def to_dict(self):
        d = {
            "detail": self.detail,
            "status": self.status,
        }

        return d


class NotFoundError(AppException):
    status = 404


class DatabaseError(AppException):
    status = 500

    def __init__(self, detail=None, **kwargs):
        super().__init__(detail=detail or "Database error occurred", **kwargs)
