import math

from storage.variant.service.KmerQueryService import KmerQueryService


def test_find_matches(kmer_query_service_with_data: KmerQueryService):
    matches_df = kmer_query_service_with_data.find_matches(['SampleA'])

    assert ['Type', 'Query', 'Match', 'Distance'] == list(matches_df.columns)
    assert ['SampleA', 'SampleC', 'SampleB'] == list(matches_df['Match'].tolist())
    assert math.isclose(0, matches_df['Distance'].tolist()[0])
    assert math.isclose(1 - 0.5, matches_df['Distance'].tolist()[1], rel_tol=1e-3)
    assert math.isclose(1 - 0.478, matches_df['Distance'].tolist()[2], rel_tol=1e-3)
