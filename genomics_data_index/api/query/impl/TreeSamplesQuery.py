from __future__ import annotations

from typing import Union, List
import logging

import pandas as pd
from ete3 import Tree, TreeStyle

from genomics_data_index.api.query.SamplesQuery import SamplesQuery
from genomics_data_index.api.query.impl.TreeBuilderReferenceMutations import TreeBuilderReferenceMutations
from genomics_data_index.api.query.impl.WrappedSamplesQuery import WrappedSamplesQuery
from genomics_data_index.api.viewer.TreeStyler import TreeStyler, DEFAULT_HIGHLIGHT_STYLES
from genomics_data_index.configuration.connector import DataIndexConnection
from genomics_data_index.storage.SampleSet import SampleSet


logger = logging.getLogger(__name__)


class TreeSamplesQuery(WrappedSamplesQuery):
    BUILD_TREE_KINDS = ['mutation']
    DISTANCE_UNITS = ['substitutions', 'substitutions/site']
    ISIN_TREE_TYPES = ['distance', 'mrca']
    MODES = ['r', 'c']

    def __init__(self, connection: DataIndexConnection, wrapped_query: SamplesQuery, tree: Tree,
                 alignment_length: int, reference_name: str, reference_included: bool):
        super().__init__(connection=connection, wrapped_query=wrapped_query)
        self._tree = tree
        self._alignment_length = alignment_length
        self._reference_name = reference_name
        self._reference_included = reference_included

    def _wrap_create(self, wrapped_query: SamplesQuery, universe_set: SampleSet = None) -> WrappedSamplesQuery:
        return TreeSamplesQuery(connection=self._query_connection,
                                wrapped_query=wrapped_query,
                                tree=self._tree,
                                alignment_length=self._alignment_length,
                                reference_name=self._reference_name,
                                reference_included=self._reference_included)

    @property
    def reference_name(self):
        return self._reference_name

    @property
    def reference_included(self):
        return self._reference_included

    def build_tree(self, kind: str, scope: str, **kwargs):
        return TreeSamplesQuery.create(kind=kind, scope=scope, database_connection=self._query_connection,
                                       wrapped_query=self, **kwargs)

    def _within_distance(self, sample_names: Union[str, List[str]], kind: str, distance: float,
                         units: str) -> SamplesQuery:
        if units == 'substitutions':
            distance_multiplier = self._alignment_length
        elif units == 'substitutions/site':
            distance_multiplier = 1
        else:
            raise Exception(f'Invalid units=[{units}]. Must be one of {self.DISTANCE_UNITS}')

        if isinstance(sample_names, list):
            raise NotImplementedError
        elif not isinstance(sample_names, str):
            raise Exception(f'Invalid type for sample_names=[{sample_names}]')

        sample_name_ids = self._get_sample_name_ids()

        sample_leaves = self._tree.get_leaves_by_name(sample_names)
        if len(sample_leaves) != 1:
            raise Exception(
                f'Invalid number of matching leaves for sample [{sample_names}], leaves {sample_leaves}')

        sample_node = sample_leaves[0]

        found_samples_set = set()
        leaves = self._tree.get_leaves()
        for leaf in leaves:
            if leaf.name not in sample_name_ids:
                continue
            sample_distance_to_other_sample = sample_node.get_distance(leaf) * distance_multiplier

            if sample_distance_to_other_sample <= distance:
                found_samples_set.add(sample_name_ids[leaf.name])

        found_samples = SampleSet(found_samples_set)
        return self.intersect(found_samples, f'within({distance} {units} of {sample_names})')

    def _within_mrca(self, sample_names: Union[str, List[str]]) -> SamplesQuery:
        if isinstance(sample_names, str):
            sample_names = [sample_names]

        sample_name_ids = self._get_sample_name_ids()
        sample_leaves_list = []
        for name in sample_names:
            sample_leaves = self._tree.get_leaves_by_name(name)
            if len(sample_leaves) != 1:
                raise Exception(
                    f'Invalid number of matching leaves for sample [{name}], leaves {sample_leaves}')
            else:
                sample_leaves_list.append(sample_leaves[0])

        if len(sample_leaves_list) == 0:
            raise Exception(f'Should at least have some leaves in the tree matching sample_names={sample_names}')
        elif len(sample_leaves_list) == 1:
            found_sample_names = sample_names
        else:
            first_sample_leaf = sample_leaves_list.pop()
            ancestor_node = first_sample_leaf.get_common_ancestor(sample_leaves_list)
            found_sample_names = ancestor_node.get_leaf_names()

        found_samples_list = []
        for name in found_sample_names:
            if name in sample_name_ids:
                found_samples_list.append(sample_name_ids[name])
        found_samples = SampleSet(found_samples_list)
        return self.intersect(found_samples, f'within(mrca of {sample_names})')

    def _isin_internal(self, data: Union[str, List[str], pd.Series], kind: str, **kwargs) -> SamplesQuery:
        if kind == 'distance':
            return self._within_distance(sample_names=data, kind=kind, **kwargs)
        elif kind == 'mrca':
            return self._within_mrca(sample_names=data)
        else:
            raise Exception(f'kind=[{kind}] is not supported. Must be one of {self._isin_kinds()}')

    def _isin_kinds(self) -> List[str]:
        return super()._isin_kinds() + self.ISIN_TREE_TYPES

    def tree_styler(self, mode = 'r',
                    initial_style: TreeStyle = None,
                    highlight_styles=DEFAULT_HIGHLIGHT_STYLES,
                    legend_nsize: int = 10, legend_fsize: int = 11,
                    annotate_color_present: str = '#66c2a4',
                    annotate_color_absent: str = 'white',
                    annotate_border_color: str = 'black',
                    annotate_kind: str = 'rect',
                    annotate_box_width: int = None,
                    annotate_box_height: int = None,
                    annotate_border_width: int = 1,
                    annotate_margin: int = 0,
                    annotate_guiding_lines: bool = True,
                    annotate_guiding_lines_color: str = 'gray',
                    figure_margin: int = None,
                    show_border: bool = True) -> TreeStyler:
        if initial_style is not None:
            if mode is not None or annotate_guiding_lines is not None or figure_margin is not None or show_border:
                logger.warning(f'Both initial_style=[{initial_style}] and mode=[{mode}] or'
                               f' annotate_guiding_lines=[{annotate_guiding_lines}] '
                               f'or figure_margin=[{figure_margin}] are set.'
                               f' Will ignore mode and annotate_guiding_lines and figure_margin.')
            ts = initial_style
        else:
            ts = TreeStyle()

            if mode is not None and mode not in self.MODES:
                raise Exception(f'Invalid value mode=[{mode}]. Must be one of {self.MODES}')
            elif mode is not None:
                ts.mode = mode

            ts.draw_guiding_lines = annotate_guiding_lines
            ts.guiding_lines_color = annotate_guiding_lines_color
            ts.show_border = show_border

            if figure_margin is None:
                figure_margin = 10

            ts.margin_top = figure_margin
            ts.margin_bottom = figure_margin
            ts.margin_left = figure_margin
            ts.margin_right = figure_margin

        # Setup default box width/height here
        if annotate_box_height is None and annotate_box_width is None:
            annotate_box_height = 30
            annotate_box_width = 30
        elif annotate_box_height is None:
            annotate_box_height = annotate_box_width
        elif annotate_box_width is None:
            annotate_box_width = annotate_box_height

        return TreeStyler(tree=self._tree.copy(method='deepcopy'),
                          default_highlight_styles=highlight_styles,
                          tree_style=ts,
                          legend_nsize=legend_nsize,
                          legend_fsize=legend_fsize,
                          annotate_column=1,
                          annotate_color_present=annotate_color_present,
                          annotate_color_absent=annotate_color_absent,
                          annotate_border_color=annotate_border_color,
                          annotate_kind=annotate_kind,
                          annotate_box_width=annotate_box_width,
                          annotate_box_height=annotate_box_height,
                          annotate_border_width=annotate_border_width,
                          annotate_margin=annotate_margin)

    @property
    def tree(self):
        return self._tree

    @classmethod
    def create(cls, kind: str, scope: str, database_connection: DataIndexConnection,
               wrapped_query: SamplesQuery, include_reference=True, **kwargs) -> TreeSamplesQuery:
        if kind == 'mutation':
            tree_builder = TreeBuilderReferenceMutations(database_connection,
                                                         reference_name=scope)
            tree, alignment_length, tree_samples_set = tree_builder.build(wrapped_query.sample_set,
                                                                          include_reference=include_reference,
                                                                          **kwargs)

            wrapped_query_tree_set = wrapped_query.intersect(sample_set=tree_samples_set,
                                                             query_message=f'mutation_tree({scope})')
            tree_samples_query = TreeSamplesQuery(connection=database_connection,
                                                  wrapped_query=wrapped_query_tree_set,
                                                  tree=tree,
                                                  alignment_length=alignment_length,
                                                  reference_name=scope,
                                                  reference_included=include_reference)
            return tree_samples_query
        else:
            raise Exception(f'Got kind=[{kind}], only the following kinds are supported: {cls.BUILD_TREE_KINDS}')
