from typing import Optional

from model.sample import Sample


class SampleRepository:
    def __init__(self) -> None:
        self._store: dict[str, Sample] = {}

    def save(self, sample: Sample) -> None:
        self._store[sample.sample_id] = sample

    def find_by_id(self, sample_id: str) -> Optional[Sample]:
        return self._store.get(sample_id)

    def find_all(self) -> list[Sample]:
        return sorted(self._store.values(), key=lambda s: s.sample_id)

    def exists(self, sample_id: str) -> bool:
        return sample_id in self._store

    def update_stock(self, sample_id: str, delta: int) -> None:
        self._store[sample_id].stock += delta
