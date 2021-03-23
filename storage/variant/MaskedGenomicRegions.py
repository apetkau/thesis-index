from __future__ import annotations
from typing import List, Set
import tempfile

from pathlib import Path
from pybedtools import BedTool
from Bio.SeqRecord import SeqRecord
from Bio import SeqIO


class MaskedGenomicRegions:

    def __init__(self, mask: BedTool):
        self._mask = mask.sort().merge()

    def intersect(self, other: MaskedGenomicRegions) -> MaskedGenomicRegions:
        return MaskedGenomicRegions(self._mask.intersect(other._mask))

    def union(self, other: MaskedGenomicRegions) -> MaskedGenomicRegions:
        union = self._mask.cat(other._mask, postmerge=True, force_truncate=True)
        return MaskedGenomicRegions(union)

    def mask_genome(self, genome_file: Path, mask_char: str = '?') -> Dict[str, SeqRecord]:
        """
        Gets a SeqRecord with all those regions on the passed genome that are in the masked regions removed.
        :param genome_file: The genome file to mask.
        :param mask_char: The character to mask with.
        :return: A Dictionary mapping a sequence name to a SeqRecord containing all those regions on the sequence
                 within the masked regions removed.
        """
        with tempfile.TemporaryDirectory() as out_f:
            seq_records = {}
            output_fasta = Path(out_f) / 'masked.fasta'
            self._mask.mask_fasta(fi=str(genome_file), fo=str(output_fasta), mc=mask_char)
            for record in SeqIO.parse(output_fasta, 'fasta'):
                record.seq = record.seq.ungap(mask_char)
                seq_records[record.id] = record
            return seq_records

    def write(self, file: Path):
        self._mask.saveas(str(file), compressed=True)

    @classmethod
    def union_all(cls, masked_regions: List[MaskedGenomicRegions]):
        if len(masked_regions) == 0:
            raise Exception('Cannot merge empty list')
        elif len(masked_regions) == 1:
            return masked_regions[0]
        else:
            start_mask = masked_regions.pop()
            union = start_mask._mask.cat(*[o._mask for o in masked_regions], postmerge=True, force_truncate=True)
            return MaskedGenomicRegions(union)

    @classmethod
    def from_sequences(cls, sequences: List[SeqRecord]) -> MaskedGenomicRegions:
        def is_missing(char):
            return char.upper() == 'N' or char == '-'

        # pybedtools internally stores as 0-based BED file intervals
        # https://daler.github.io/pybedtools/intervals.html#bed-is-0-based-others-are-1-based
        mask_intervals = []

        for record in sequences:
            start = 0
            in_mask = False
            for idx, char in enumerate(record.seq):
                if in_mask:
                    if not is_missing(char):
                        in_mask = False
                        # pybedtools stop position is not included in interval
                        stop = idx
                        mask_intervals.append((record.id, start, stop))
                else:
                    if is_missing(char):
                        in_mask = True
                        start = idx

            # Finish recording last interval if it exists (e.g., if last bit of sequence was like 'NNNN')
            if in_mask:
                stop = len(record)
                mask_intervals.append((record.id, start, stop))

        bedtool_intervals = BedTool(mask_intervals)
        return MaskedGenomicRegions(bedtool_intervals)

    @classmethod
    def from_file(cls, file: Path) -> MaskedGenomicRegions:
        bed_file_data = BedTool(str(file))
        return MaskedGenomicRegions(bed_file_data)

    @classmethod
    def empty_mask(cls):
        return MaskedGenomicRegions(BedTool('', from_string=True))

    def is_empty(self):
        return len(self) == 0

    def sequence_names(self) -> Set[str]:
        """
        Gets a set of sequence names from this genomic regions mask.
        :return: A set of sequence names.
        """
        return {x.chrom for x in self._mask}

    def contains(self, sequence: str, position: int) -> bool:
        for i in self._mask:
            if i.chrom == sequence and i.start <= position < i.end:
                return True
        return False

    def __len__(self) -> int:
        """
        Calculates length of underlying masked intervals. Assumes the intervals have been merged beforehand.
        :return: The length of the masked intervals.
        """
        total = 0
        for i in self._mask:
            total += len(i)
        return total
