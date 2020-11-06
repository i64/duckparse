from dataclasses import dataclass


@dataclass
class ValidationError(Exception):
    expected: bytes
    found: bytes

    def __str__(self):
        return (
            f"expected {list(self.expected)}, found {list(self.found)} "
        )
