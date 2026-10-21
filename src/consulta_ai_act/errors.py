"""Safe application exceptions that do not contain user-provided text."""


class ApplicationError(Exception):
    """Base class for expected application errors with safe messages."""


class ConfigurationError(ApplicationError):
    """Raised when required or valid runtime configuration is unavailable."""


class SourceIngestionError(ApplicationError):
    """Raised when a source document cannot be parsed completely."""


class CitationValidationError(ApplicationError):
    """Raised when generated citations are not supported by retrieved evidence."""