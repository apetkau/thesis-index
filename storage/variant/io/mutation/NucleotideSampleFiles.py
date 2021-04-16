from abc import ABC
from typing import Tuple, Optional
from pathlib import Path

from storage.variant.io.SampleFiles import SampleFiles
from storage.variant.MaskedGenomicRegions import MaskedGenomicRegions
from storage.variant.io.mutation.VariationFile import VariationFile


class NucleotideSampleFiles(SampleFiles):

    def __init__(self, sample_name: str, vcf_file: Path, vcf_file_index: Path,
                 mask_bed_file: Optional[Path],
                 preprocessed: bool,
                 tmp_dir: Path):
        super().__init__(sample_name=sample_name)
        self._vcf_file = vcf_file
        self._vcf_file_index = vcf_file_index
        self._tmp_dir = tmp_dir
        self._preprocessed = preprocessed
        self._mask_bed_file = mask_bed_file

    def _preprocess_mask(self) -> Path:
        if self._mask_bed_file is None:
            raise Exception('mask_bed_file does not exist')
        else:
            return self._mask_bed_file

    def _do_preprocess(self) -> SampleFiles:
        processed_vcf, processed_vcf_index = self._preprocess_vcf()
        processed_mask = self._preprocess_mask()

        return NucleotideSampleFiles(sample_name=self.sample_name,
                                     vcf_file=processed_vcf,
                                     vcf_file_index=processed_vcf_index,
                                     mask_bed_file=processed_mask,
                                     preprocessed=True,
                                     tmp_dir=self._tmp_dir)

    def is_preprocessed(self) -> bool:
        return self._preprocessed

    def _preprocess_vcf(self) -> Tuple[Path, Path]:
        new_file = self._tmp_dir / f'{self.sample_name}.vcf.gz'
        return VariationFile(self._vcf_file).write(new_file)

    def get_vcf_file(self, ignore_preprocessed = False) -> Tuple[Path, Path]:
        if ignore_preprocessed or self._preprocessed:
            return self._vcf_file, self._vcf_file_index
        else:
            raise Exception(f'VCF file for sample [{self.sample_name}] is not preprocessed: {self._vcf_file}')

    def get_mask(self) -> MaskedGenomicRegions:
        if self._preprocessed and self._mask_bed_file is not None:
            return MaskedGenomicRegions.from_file(self._mask_bed_file)
        else:
            raise Exception(f'Sample mask file is not preprocessed for sample [{self.sample_name}]')