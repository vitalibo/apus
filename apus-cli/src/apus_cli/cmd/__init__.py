import abc


class Command(abc.ABC):
    """Abstract base class for CLI commands."""

    @abc.abstractmethod
    def execute(self):
        """Execute the command."""
