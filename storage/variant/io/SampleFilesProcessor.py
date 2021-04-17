import abc
from typing import Generator, List

from storage.variant.io.SampleData import SampleData


class SampleFilesProcessor(abc.ABC):

    def __init__(self):
        self._sample_files_list = []

    def add(self, sample_files: SampleData) -> None:
        self._sample_files_list.append(sample_files)

    def sample_files_list(self) -> List[SampleData]:
        return self._sample_files_list

    @abc.abstractmethod
    def preprocess_files(self) -> Generator[SampleData, None, None]:
        pass
