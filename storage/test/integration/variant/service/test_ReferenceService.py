from pathlib import Path
from os import path

from storage.variant.service.ReferenceService import ReferenceService
from storage.variant.model import Reference
from storage.variant.service import DatabaseConnection

data_dir = Path(path.dirname(__file__), '..', '..', 'data', 'snippy')
reference_file = data_dir / 'genome.fasta.gz'


def test_insert_reference_genome():
    database = DatabaseConnection('sqlite:///:memory:')
    reference_service = ReferenceService(database)

    assert 0 == database.get_session().query(Reference).count(), 'Database should be empty initially'
    reference_service.create_reference_genome(reference_file)
    assert 1 == database.get_session().query(Reference).count(), 'Database should have one entry'
    assert 'genome' == database.get_session().query(Reference).all()[0].name, 'Name should match'


def test_find_reference_genome():
    database = DatabaseConnection('sqlite:///:memory:')
    reference_service = ReferenceService(database)

    assert 0 == database.get_session().query(Reference).count(), 'Database should be empty initially'
    reference_service.create_reference_genome(reference_file)

    reference = reference_service.find_reference_genome('genome')
    assert 'genome' == reference.name, 'Reference name should match'
    assert 5180 == reference.length, 'Reference length should match'