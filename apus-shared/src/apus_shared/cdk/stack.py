from __future__ import annotations

import abc
import typing

if typing.TYPE_CHECKING:
    from aws_cdk import Stack

    from apus_shared.models import Resource


class StackBuilder(abc.ABC):
    """AWS CDK Stack Builder base class."""

    @abc.abstractmethod
    def build(self, stack: Stack, resources: list[Resource]) -> None:
        """Build CDK resources in the stack."""


def register(builder: StackBuilder) -> None:
    """Register a StackBuilder implementation."""

    builders.append(builder)


builders: typing.Final[list[StackBuilder]] = []
