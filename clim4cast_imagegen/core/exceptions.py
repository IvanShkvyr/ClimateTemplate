
from typing import List


class Clim4CastError(Exception):
    """Basic domain exception."""


class UploadIncompleteError(Clim4CastError):
    def __init__(self, failed: List):
        self.failed = failed
        super().__init__(f"{len(failed)} file(s) failed to upload after retries")


class InvalidRasterDateError(Clim4CastError):
    def __init__(self, path):
        self.path = path
        super().__init__(f"Cannot extract a valid date from filename: {path}")
