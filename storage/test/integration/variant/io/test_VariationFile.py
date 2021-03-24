import tempfile
from pathlib import Path

from storage.test.integration.variant import data_dir, variation_dir, reference_file, consensus_dir
from storage.variant.io.VariationFile import VariationFile
from storage.variant.MaskedGenomicRegions import MaskedGenomicRegions
from storage.variant.util import parse_sequence_file


def test_write():
    sample_vcf = data_dir / 'SampleA' / 'snps.vcf.gz'
    with tempfile.TemporaryDirectory() as out_dir:
        out_file = Path(out_dir) / 'out.bcf'

        assert not out_file.exists()
        VariationFile(sample_vcf).write(out_file)
        assert out_file.exists()


def test_consensus_no_mask():
    sample_bcf = variation_dir / 'SampleA.bcf'

    expected_consensus_file = consensus_dir / 'SampleA-consensus-nomask.fasta.gz'
    name, expected_consensus_records = parse_sequence_file(expected_consensus_file)
    expected_consensus_record = expected_consensus_records[0]

    seq_records = VariationFile(sample_bcf).consensus(reference_file=reference_file)
    
    assert 1 == len(seq_records)
    actual_seq_record = seq_records[0]
    assert 5180 == len(actual_seq_record)
    assert expected_consensus_record.id == actual_seq_record.id
    assert expected_consensus_record.seq == actual_seq_record.seq


def test_consensus_empty_mask():
    sample_bcf = variation_dir / 'SampleA.bcf'
    empty_mask = MaskedGenomicRegions.empty_mask()

    expected_consensus_file = consensus_dir / 'SampleA-consensus-nomask.fasta.gz'
    name, expected_consensus_records = parse_sequence_file(expected_consensus_file)
    expected_consensus_record = expected_consensus_records[0]

    with tempfile.TemporaryDirectory() as out_dir:
        mask_file = Path(out_dir) / 'mask.bed.gz'
        empty_mask.write(mask_file)

        seq_records = VariationFile(sample_bcf).consensus(reference_file=reference_file,
                                            mask_file=mask_file)
        assert 1 == len(seq_records)
        actual_seq_record = seq_records[0]
        assert 5180 == len(actual_seq_record)
        assert expected_consensus_record.id == actual_seq_record.id
        assert expected_consensus_record.seq == actual_seq_record.seq


def test_consensus_mask():
    sample_bcf = variation_dir / 'SampleA.bcf'
    sample_mask_file = variation_dir / 'SampleA.bed.gz'

    expected_consensus_file = consensus_dir / 'SampleA-consensus-withmask.fasta.gz'
    name, expected_consensus_records = parse_sequence_file(expected_consensus_file)
    expected_consensus_record = expected_consensus_records[0]

    seq_records = VariationFile(sample_bcf).consensus(reference_file=reference_file,
                                        mask_file=sample_mask_file)
    assert 1 == len(seq_records)
    actual_seq_record = seq_records[0]
    assert 5180 == len(actual_seq_record)
    assert expected_consensus_record.id == actual_seq_record.id
    assert expected_consensus_record.seq == actual_seq_record.seq


def test_consensus_mask_over_mutation():
    sample_bcf = variation_dir / 'SampleA.bcf'
    sample_mask_file = variation_dir / 'SampleA-mask-over-mutation.bed.gz'

    expected_consensus_file = consensus_dir / 'SampleA-consensus-withmask-over-mutation.fasta.gz'
    name, expected_consensus_records = parse_sequence_file(expected_consensus_file)
    expected_consensus_record = expected_consensus_records[0]

    seq_records = VariationFile(sample_bcf).consensus(reference_file=reference_file,
                                        mask_file=sample_mask_file)
    assert 1 == len(seq_records)
    actual_seq_record = seq_records[0]
    assert 5180 == len(actual_seq_record)
    assert expected_consensus_record.id == actual_seq_record.id
    assert expected_consensus_record.seq == actual_seq_record.seq


def test_union_all_files():
    # List like this to guarantee a specific order
    variant_files = [
        data_dir / 'SampleA' / 'snps.vcf.gz',
        data_dir / 'SampleB' / 'snps.vcf.gz',
        data_dir / 'SampleC' / 'snps.vcf.gz'
    ]
    union_df = VariationFile.union_all_files(variant_files)

    assert 60 == len(union_df)
    assert '010' == union_df[(union_df['CHROM'] == 'reference') & (union_df['POS'] == 190)]['INDEXES'].values[0]
    assert '010' == union_df[(union_df['CHROM'] == 'reference') & (union_df['POS'] == 5061)]['INDEXES'].values[0]
    assert '011' == union_df[(union_df['CHROM'] == 'reference') & (union_df['POS'] == 4975)]['INDEXES'].values[0]
    assert '100' == union_df[(union_df['CHROM'] == 'reference') & (union_df['POS'] == 2076)]['INDEXES'].values[0]


def test_union_one_file():
    sample_bcf = variation_dir / 'SampleA.bcf'
    union_df = VariationFile.union_all_files([sample_bcf])

    assert 26 == len(union_df)
    assert '1' == union_df[(union_df['CHROM'] == 'reference') & (union_df['POS'] == 293)]['INDEXES'].values[0]
    assert '1' == union_df[(union_df['CHROM'] == 'reference') & (union_df['POS'] == 4929)]['INDEXES'].values[0]
