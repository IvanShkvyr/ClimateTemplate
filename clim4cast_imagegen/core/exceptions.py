
from typing import List


class Clim4CastError(Exception):
    """Basic domain exception."""


class UploadIncompleteError(Clim4CastError):
    def __init__(self, failed: List):
        self.failed = failed
        super().__init__(f"{len(failed)} file(s) failed to upload after retries")