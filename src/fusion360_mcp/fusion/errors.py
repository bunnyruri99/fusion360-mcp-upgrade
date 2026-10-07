"""Domain errors — each is a distinct failure mode, not a generic Exception."""


class FusionError(Exception):
    """Base class for all Fusion bridge errors."""


class FusionConnectionError(FusionError):
    """Add-in is not running or port is wrong."""


class FusionTimeoutError(FusionError):
    """Operation exceeded the configured timeout."""


class FusionOperationError(FusionError):
    """Fusion API rejected the operation (e.g. no active design, bad profile)."""
