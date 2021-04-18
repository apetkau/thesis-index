from typing import Generator, Set

from storage.variant.io.SampleData import SampleData
from storage.variant.io.SampleDataPackage import SampleDataPackage
from storage.variant.io.mlst.MLSTFeaturesReader import MLSTFeaturesReader
from storage.variant.io.mlst.MLSTSampleData import MLSTSampleData


class MLSTSampleDataPackage(SampleDataPackage):

    def __init__(self, mlst_reader: MLSTFeaturesReader):
        super().__init__()
        self._mlst_reader = mlst_reader

    def get_features_reader(self) -> MLSTFeaturesReader:
        return self._mlst_reader

    def sample_names(self) -> Set[str]:
        return set(self._mlst_reader.samples_list())

    def iter_sample_data(self) -> Generator[SampleData, None, None]:
        for sample_name, scheme, data in self._mlst_reader.iter_sample_data():
            yield MLSTSampleData(sample_name=sample_name, scheme=scheme, mlst_allele_data=data)