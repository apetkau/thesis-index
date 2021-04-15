import logging
from pathlib import Path
from typing import Dict, Set, Any, Tuple, cast

import pandas as pd

from storage.variant.SampleSet import SampleSet
from storage.variant.io.FeaturesReader import FeaturesReader
from storage.variant.io.mlst.MLSTFeaturesReader import MLSTFeaturesReader
from storage.variant.model.db import MLSTScheme, SampleMLSTAlleles, MLSTAllelesSamples, Sample
from storage.variant.service import DatabaseConnection
from storage.variant.service.FeatureService import FeatureService, AUTO_SCOPE
from storage.variant.service.SampleService import SampleService

logger = logging.getLogger(__name__)


class MLSTService(FeatureService):

    def __init__(self, database_connection: DatabaseConnection, sample_service: SampleService, mlst_dir: Path):
        super().__init__(database_connection=database_connection,
                         features_dir=mlst_dir,
                         sample_service=sample_service)
        self._database = database_connection
        self._sample_service = sample_service

    def find_mlst_scheme(self, name: str) -> MLSTScheme:
        return self._database.get_session().query(MLSTScheme) \
            .filter(MLSTScheme.name == name) \
            .one()

    def exists_mlst_scheme(self, name: str):
        return self._connection.get_session().query(MLSTScheme.id).filter_by(name=name).scalar() is not None

    def get_or_create_mlst_scheme(self, name: str) -> MLSTScheme:
        if self.exists_mlst_scheme(name):
            return self.find_mlst_scheme(name)
        else:
            return MLSTScheme(name=name)

    def find_mlst_schemes(self, scheme_names: Set[str]) -> Dict[str, MLSTScheme]:
        schemes = {}
        for name in scheme_names:
            scheme = self.find_mlst_scheme(name)
            schemes[name] = scheme

        return schemes

    def get_all_alleles(self, scheme: str, locus: str) -> Set[str]:
        return {a for a, in self._database.get_session().query(MLSTAllelesSamples.allele) \
            .filter(MLSTAllelesSamples.scheme == scheme, MLSTAllelesSamples.locus == locus) \
            .all()}

    def get_all_loci_alleles(self, scheme: str) -> Set[Tuple[str, str]]:
        """
        Gets all (loci, allele) pairs from the database given a scheme.
        :param scheme: The scheme.
        :return: Gets a list of tuples of the form (loci, allele).
        """
        return {a for a in self._database.get_session().query(MLSTAllelesSamples.locus, MLSTAllelesSamples.allele) \
            .filter(MLSTAllelesSamples.scheme == scheme) \
            .all()}

    def _create_feature_identifier(self, features_df: pd.DataFrame) -> str:
        return MLSTAllelesSamples.to_sla(
            scheme_name=features_df['Scheme'],
            locus=features_df['Locus'],
            allele=features_df['Allele']
        )

    def aggregate_feature_column(self) -> Dict[str, Any]:
        return {'_SAMPLE_ID': SampleSet}

    def _get_sample_id_series(self, features_df: pd.DataFrame, sample_name_ids: Dict[str, int]) -> pd.Series:
        return features_df.apply(lambda x: sample_name_ids[x['Sample']], axis='columns')

    def _create_feature_object(self, features_df: pd.DataFrame):
        return MLSTAllelesSamples(sla=features_df['_FEATURE_ID'], sample_ids=features_df['_SAMPLE_ID'])

    def check_samples_have_features(self, sample_names: Set[str], feature_scope_name: str) -> bool:
        samples_with_mlst = {sample.name for sample in
                             self._sample_service.get_samples_with_mlst_alleles(feature_scope_name)}
        return len(samples_with_mlst.intersection(sample_names)) != 0

    def get_correct_reader(self) -> Any:
        return MLSTFeaturesReader

    def _update_scope(self, features_df: pd.DataFrame, feature_scope_name: str) -> pd.DataFrame:
        if feature_scope_name != AUTO_SCOPE:
            features_df['Scheme'] = feature_scope_name
        return features_df

    def build_sample_feature_object(self, sample: Sample, features_reader: FeaturesReader,
                                    feature_scope_name: str) -> Any:
        self._verify_correct_reader(features_reader=features_reader)
        mlst_reader = cast(MLSTFeaturesReader, features_reader)

        if feature_scope_name == AUTO_SCOPE:
            scheme_name = mlst_reader.get_scheme_for_sample(sample.name)
        else:
            scheme_name = feature_scope_name

        mlst_scheme = self.get_or_create_mlst_scheme(scheme_name)
        sample_mlst_alleles = SampleMLSTAlleles(sample=sample, scheme=mlst_scheme)

        return sample_mlst_alleles