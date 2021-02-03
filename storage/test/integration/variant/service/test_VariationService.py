import math

from storage.variant.model import VariationAllele
from storage.variant.service.VariationService import VariationService


def test_insert_variants(database, snippy_variants_reader, ref_contigs):
    variation_service = VariationService(database)

    core_masks = snippy_variants_reader.get_core_masks()
    var_df = snippy_variants_reader.get_variants_table()
    session = database.get_session()

    variation_service.insert_variants(var_df=var_df,
                                               ref_contigs=ref_contigs,
                                               core_masks=core_masks)

    assert 112 == session.query(VariationAllele).count(), 'Incorrect number of variant entries'

    # Check to make sure some variation alleles are stored
    v = session.query(VariationAllele).get('reference:1048:C:G')
    assert v is not None, 'Particular variant does not exist'
    assert 1048 == v.position, 'Position is incorrect'
    assert 'C' == v.ref, 'Reference is incorrect'
    assert 'G' == v.alt, 'Alt is incorrect'
    assert 'reference' == v.sequence.sequence_name, 'Sequence name is incorrect'
    assert 5180 == v.sequence.sequence_length, 'Sequence length is incorrect'
    assert 'snp' == v.var_type, 'Type is incorrect'

    v = session.query(VariationAllele).get('reference:1135:CCT:C')
    assert v is not None, 'Particular variant does not exist'
    assert 1135 == v.position, 'Position is incorrect'
    assert 'CCT' == v.ref, 'Reference is incorrect'
    assert 'C' == v.alt, 'Alt is incorrect'
    assert 'reference' == v.sequence.sequence_name, 'Sequence name is incorrect'
    assert 5180 == v.sequence.sequence_length, 'Sequence length is incorrect'
    assert 'del' == v.var_type, 'Type is incorrect'


def test_pariwise_distance(database, snippy_variants_reader, ref_contigs):
    variation_service = VariationService(database)

    core_masks = snippy_variants_reader.get_core_masks()
    var_df = snippy_variants_reader.get_variants_table()

    variation_service.insert_variants(var_df=var_df,
                                      ref_contigs=ref_contigs,
                                      core_masks=core_masks)

    distances = variation_service.pairwise_distance(['SampleA', 'SampleC', 'SampleB'])

    expected_distAB = 1
    expected_distAC = 1
    expected_distBC = (1 - 17 / 66)

    assert math.isclose(expected_distAB, distances.loc['SampleA', 'SampleB']), 'Incorrect pairwise distance'
    assert math.isclose(expected_distAC, distances.loc['SampleA', 'SampleC']), 'Incorrect pairwise distance'
    assert math.isclose(expected_distBC, distances.loc['SampleB', 'SampleC']), 'Incorrect pairwise distance'
