from typing import List
from pathlib import Path
from os import path
import logging
import yaml
import pandas as pd

from genomics_data_index.pipelines.PipelineExecutor import PipelineExecutor
from genomics_data_index.storage.util import execute_commands

logger = logging.getLogger(__name__)


snakemake_file = Path(path.dirname(__file__), 'assembly_input', 'workflow', 'Snakefile')


class SnakemakePipelineExecutor(PipelineExecutor):

    def __init__(self, working_directory: Path):
        super().__init__()
        self._working_directory = working_directory

    def _sample_name_from_file(self, sample_file: Path) -> str:
        return sample_file.stem

    def _prepare_working_directory(self, reference_file: Path,
                                   input_files: List[Path]) -> Path:
        config_dir = self._working_directory / 'config'
        config_dir.mkdir()

        config_file = config_dir / 'config.yaml'
        samples_file = config_dir / 'samples.tsv'

        logger.debug(f'Writing snakemake config [{config_file}]')
        with open(config_file, 'w') as fh:
            config = {
                'reference': str(reference_file),
                'samples': str(samples_file)
            }
            yaml.dump(config, fh)

        logger.debug(f'Writing samples list [{samples_file}]')

        sample_names = []
        for file in input_files:
            sample_names.append([self._sample_name_from_file(file), str(file)])

        sample_names_df = pd.DataFrame(sample_names, columns=['Sample', 'File'])
        sample_names_df.to_csv(samples_file, sep='\t', index=False)

        return config_file

    def execute(self, input_files: List[Path], reference_file: Path, ncores: int = 1) -> Path:
        working_directory = self._working_directory
        logger.debug(f'Preparing working directory [{working_directory}] for snakemake')
        config_file = self._prepare_working_directory(reference_file=reference_file,
                                                      input_files=input_files)

        logger.debug(f'Executing snakemake on {len(input_files)} files with reference_file=[{reference_file}]'
                     f' using {ncores} cores in [{working_directory}]')
        snakemake_output = working_directory / 'gdi-input.fofn'
        command = ['snakemake', '--configfile', str(config_file), '--use-conda', '-j', str(ncores), '--directory', str(working_directory),
                   '--snakefile', str(snakemake_file)]
        execute_commands([command])
        logger.debug(f'Finished executing snakemake. Output file [{snakemake_output}]')

        return snakemake_output