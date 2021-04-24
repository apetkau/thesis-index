from __future__ import annotations

import pandas as pd
from storage.api.impl.TreeSamplesQuery import TreeSamplesQuery

from storage.api.SamplesQuery import SamplesQuery
from storage.api.impl.WrappedSamplesQuery import WrappedSamplesQuery
from storage.configuration.connector import DataIndexConnection
from storage.variant.SampleSet import SampleSet


class DataFrameSamplesQuery(WrappedSamplesQuery):

    def __init__(self, connection: DataIndexConnection, wrapped_query: SamplesQuery,
                 universe_set: SampleSet,
                 data_frame: pd.DataFrame,
                 sample_ids_col: str):
        super().__init__(connection=connection, wrapped_query=wrapped_query, universe_set=universe_set)
        self._sample_ids_col = sample_ids_col
        self._data_frame = data_frame

    def toframe(self, exclude_absent: bool = True) -> pd.DataFrame:
        samples_dataframe = super().toframe()
        samples_df_cols = list(samples_dataframe.columns)
        merged_df = self._data_frame.merge(samples_dataframe, how='inner', left_on=self._sample_ids_col,
                                           right_on='Sample ID')
        new_col_order = samples_df_cols + [col for col in list(merged_df.columns) if col not in samples_df_cols]
        return merged_df[new_col_order]

    def _wrap_create(self, wrapped_query: SamplesQuery) -> WrappedSamplesQuery:
        return DataFrameSamplesQuery(connection=self._query_connection,
                                     wrapped_query=wrapped_query,
                                     data_frame=self._data_frame,
                                     sample_ids_col=self._sample_ids_col,
                                     universe_set=self.universe_set)

    def build_tree(self, kind: str, scope: str, **kwargs) -> SamplesQuery:
        return TreeSamplesQuery.create(kind=kind, scope=scope, database_connection=self._query_connection,
                                       wrapped_query=self, **kwargs)

    @classmethod
    def create_with_sample_ids_column(self, sample_ids_column: str, data_frame: pd.DataFrame,
                                      wrapped_query: SamplesQuery, connection: DataIndexConnection,
                                      query_message: str = None) -> DataFrameSamplesQuery:
        sample_ids = data_frame[sample_ids_column].tolist()
        df_sample_set = SampleSet(sample_ids=sample_ids)
        universe_set = wrapped_query.universe_set.intersection(df_sample_set)

        if query_message is None:
            query_message = f'dataframe(ids_col=[{sample_ids_column}])'

        wrapped_query_intersect = wrapped_query.intersect(sample_set=df_sample_set,
                                                          query_message=query_message)

        return DataFrameSamplesQuery(connection=connection,
                                     wrapped_query=wrapped_query_intersect,
                                     universe_set=universe_set,
                                     data_frame=data_frame,
                                     sample_ids_col=sample_ids_column)

    def join(self, data_frame: pd.DataFrame, sample_ids_column: str = None,
             sample_names_column: str = None) -> SamplesQuery:
        raise Exception(f'Cannot join a new dataframe onto an existing data frame query: {self}')

    @classmethod
    def create_with_sample_names_column(self, sample_names_column: str, data_frame: pd.DataFrame,
                                        wrapped_query: SamplesQuery,
                                        connection: DataIndexConnection) -> DataFrameSamplesQuery:
        sample_names = set(data_frame[sample_names_column].tolist())
        sample_ids_column = 'Sample ID'

        sample_name_ids = connection.sample_service.find_sample_name_ids(sample_names)

        # Only attempt once to rename sample IDs column if it already exists
        if sample_ids_column in data_frame:
            sample_ids_column = sample_ids_column + '_gdi'
            if sample_ids_column in data_frame:
                raise Exception(f'Column to be used for sample_ids [{sample_ids_column}] already in data frame')

        sample_ids_series = pd.Series(sample_name_ids, name=sample_ids_column)
        data_frame = data_frame.merge(sample_ids_series, left_on=sample_names_column, right_index=True)

        query_message = f'dataframe(names_col=[{sample_names_column}])'

        return DataFrameSamplesQuery.create_with_sample_ids_column(sample_ids_column=sample_ids_column,
                                                                   data_frame=data_frame,
                                                                   wrapped_query=wrapped_query,
                                                                   connection=connection,
                                                                   query_message=query_message)
