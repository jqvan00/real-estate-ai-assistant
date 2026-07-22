from typing import Protocol


class PropertyConnector(Protocol):
    name: str

    def fetch(self, address: str, listing_url: str | None = None) -> dict:
        ...
