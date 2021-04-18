import tempfile
from pathlib import Path
import warnings

import pytest
from storage.variant.io.mlst.MLSTTSeemannFeaturesReader import MLSTTSeemannFeaturesReader

from storage.variant.io.mlst.MLSTSampleDataPackage import MLSTSampleDataPackage

warnings.filterwarnings("ignore", category=DeprecationWarning)

from storage.test.integration import sample_dirs, reference_file, basic_mlst_file
from storage.connector.DataIndexConnection import DataIndexConnection
from storage.variant.io.mutation.NucleotideSampleDataPackage import NucleotideSampleDataPackage
from storage.variant.io.processor.SerialSampleFilesProcessor import SerialSampleFilesProcessor


@pytest.fixture
def loaded_database_connection() -> DataIndexConnection:
    tmp_dir = Path(tempfile.mkdtemp())
    database_connection = DataIndexConnection.connect(database_connection='sqlite:///:memory:',
                                                      database_dir=tmp_dir)

    # Load Nucleotide variation
    database_connection.reference_service.add_reference_genome(reference_file)
    snippy_tmp_dir = Path(tempfile.mkdtemp())
    data_package = NucleotideSampleDataPackage.create_from_snippy(sample_dirs,
                                                                  SerialSampleFilesProcessor(snippy_tmp_dir))
    database_connection.variation_service.insert(data_package, feature_scope_name='genome')

    # Load MLST
    mlst_package = MLSTSampleDataPackage(MLSTTSeemannFeaturesReader(mlst_file=basic_mlst_file))
    database_connection.mlst_service.insert(mlst_package)

    return database_connection