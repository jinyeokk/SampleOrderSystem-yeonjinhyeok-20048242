from model.sample import Sample
from repository.sample_repo import SampleRepository


class DuplicateSampleIdError(Exception):
    pass


class SampleNotFoundError(Exception):
    pass


class SampleService:
    def __init__(self, repo: SampleRepository) -> None:
        self._repo = repo

    def register(
        self,
        sample_id: str,
        name: str,
        avg_production_time: float,
        yield_rate: float,
    ) -> Sample:
        if self._repo.exists(sample_id):
            raise DuplicateSampleIdError(sample_id)
        sample = Sample(
            sample_id=sample_id,
            name=name,
            avg_production_time=avg_production_time,
            yield_rate=yield_rate,
        )
        self._repo.save(sample)
        return sample

    def get(self, sample_id: str) -> Sample:
        sample = self._repo.find_by_id(sample_id)
        if sample is None:
            raise SampleNotFoundError(sample_id)
        return sample

    def get_all(self) -> list[Sample]:
        return self._repo.find_all()

    def search(self, keyword: str) -> list[Sample]:
        kw = keyword.lower()
        return [
            s for s in self._repo.find_all()
            if kw in s.sample_id.lower() or kw in s.name.lower()
        ]

    def update_stock(self, sample_id: str, delta: int) -> None:
        self._repo.update_stock(sample_id, delta)
