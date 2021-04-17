import abc
from typing import Set, List, Generator

import pandas as pd

from storage.variant.io.FeaturesReader import FeaturesReader
from storage.variant.io.SampleFiles import SampleFiles
from storage.variant.model import MLST_UNKNOWN_ALLELE


class MLSTFeaturesReader(FeaturesReader):

    def __init__(self):
        super().__init__()
        self._features_table = None

    def get_sample_files(self, sample_name: str) -> SampleFiles:
        return None

    def iter_sample_files(self) -> Generator[SampleFiles, None, None]:
        for sample in []:
            yield sample

    def get_features_table(self) -> pd.DataFrame:
        if self._features_table is None:
            self._features_table = super().get_features_table()
            self._features_table['Allele'] = self.validate_alleles(self._features_table['Allele'])
        return self._features_table

    def _minimal_expected_columns(self) -> Set[str]:
        return {'Sample', 'Scheme', 'Locus', 'Allele'}

    @abc.abstractmethod
    def _is_valid_allele(self, allele: str) -> bool:
        pass

    def validate_alleles(self, alleles_series: pd.Series) -> pd.Series:
        return_alleles = alleles_series.copy(deep=True)
        return_alleles[~alleles_series.apply(self._is_valid_allele)] = MLST_UNKNOWN_ALLELE
        return return_alleles

    def samples_list(self) -> List[str]:
        mlst_df = self.get_features_table()
        return list(set(mlst_df['Sample'].tolist()))

    def get_or_create_feature_file(self, sample_name: str):
        raise Exception('Not implemented')

    def get_scheme_for_sample(self, sample_name: str):
        mlst_df = self.get_features_table()
        scheme_set = set(mlst_df.loc[mlst_df['Sample'] == sample_name, 'Scheme'].values)
        if len(scheme_set) == 0:
            raise Exception(f'No found schemes in the MLST table for sample [{sample_name}]')
        elif len(scheme_set) == 1:
            return scheme_set.pop()
        else:
            raise Exception(f'More than one schemes found in the MLST table for sample '
                            f'[{sample_name}]: [{scheme_set}]')
