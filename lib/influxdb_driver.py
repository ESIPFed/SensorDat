import influxdb
import pandas as pd

class InfluxDBInput():
    def __init__(self, config_dict):
        self.client = influxdb.InfluxDBClient(**config_dict)

    def run_query(self, field, measurement, tags, pagesize=10000):
        collect = []
        times = []
        values = []
        q = True
        pagenum = 0
        # Single quotes around tags might not always work
        tag_str = ' AND '.join(["{key}='{value}'".format(key=key, value=value) for key, value
                                in tags.items()])
        while q:
            q = self.client.query(("SELECT {field} FROM {measurement} WHERE {tags} "
                                   "LIMIT {pagesize} OFFSET {page}")
                                   .format(field=field, measurement=measurement, tags=tag_str,
                                    pagesize=pagesize, page=pagenum*pagesize))
            if q:
                collect.append(q[measurement])
            pagenum += 1
        for resultset in collect:
            for reading in resultset:
                times.append(reading['time'])
                values.append(reading[field])
        s = pd.Series(values, index=times)
        s.index = pd.to_datetime(s.index)
        return s

    def run(self, ingredient_dict):
        return self.run_query(**ingredient_dict)

class InfluxDBOutput():
    def __init__(self, config_dict):
        self.client = influxdb.InfluxDBClient(**config_dict)

    def _stringify_dataframe(self,
                             dataframe,
                             numeric_precision,
                             datatype='field',
                             upcast_to_float=True):

        # Find int and string columns for field-type data
        int_columns = dataframe.select_dtypes(include=['integer']).columns
        string_columns = dataframe.select_dtypes(include=['object']).columns

        # Convert dataframe to string
        if numeric_precision is None:
            # If no precision specified, convert directly to string (fast)
            dataframe = dataframe.astype(str)
        elif numeric_precision == 'full':
            # If full precision, use repr to get full float precision
            float_columns = (dataframe.select_dtypes(include=['floating'])
                             .columns)
            nonfloat_columns = dataframe.columns[~dataframe.columns.isin(
                float_columns)]
            dataframe[float_columns] = dataframe[float_columns].applymap(repr)
            dataframe[nonfloat_columns] = (dataframe[nonfloat_columns]
                                           .astype(str))
        elif isinstance(numeric_precision, int):
            # If precision is specified, round to appropriate precision
            float_columns = (dataframe.select_dtypes(include=['floating'])
                             .columns)
            nonfloat_columns = dataframe.columns[~dataframe.columns.isin(
                float_columns)]
            dataframe[float_columns] = (dataframe[float_columns]
                                        .round(numeric_precision))
            # If desired precision is > 10 decimal places, need to use repr
            if numeric_precision > 10:
                dataframe[float_columns] = (dataframe[float_columns]
                                            .applymap(repr))
                dataframe[nonfloat_columns] = (dataframe[nonfloat_columns]
                                               .astype(str))
            else:
                dataframe = dataframe.astype(str)
        else:
            raise ValueError('Invalid numeric precision.')

        if datatype == 'field':
            # If dealing with fields, format ints and strings correctly
            if not upcast_to_float:
                dataframe[int_columns] = dataframe[int_columns] + 'i'
            dataframe[string_columns] = '"' + dataframe[string_columns] + '"'

        dataframe.columns = dataframe.columns.values.astype(str)
        return dataframe

    def _convert_series_to_lines(self,
                                 measurement,
                                 fields,
                                 tags=None,
                                 field_names=[],
                                 tag_names=[],
                                 global_tags={},
                                 time_precision=None,
                                 numeric_precision=None):

        if isinstance(fields, pd.Series):
            if not (isinstance(fields.index, pd.PeriodIndex) or
                    isinstance(fields.index, pd.DatetimeIndex)):
                raise TypeError('Must be Series with DatetimeIndex or \
                                PeriodIndex.')

        elif isinstance(fields, list):
            for field in fields:
                if not isinstance(field, pd.Series):
                    raise TypeError('Must be Series, but type was: {0}.'
                                    .format(type(field)))
                if not (isinstance(field.index, pd.tseries.period.PeriodIndex) or
                        isinstance(field.index, pd.tseries.index.DatetimeIndex)):
                    raise TypeError('Must be Series with DatetimeIndex or \
                                    PeriodIndex.')

        precision_factor = {
            "n": 1,
            "u": 1e3,
            "ms": 1e6,
            "s": 1e9,
            "m": 1e9 * 60,
            "h": 1e9 * 3600,
        }.get(time_precision, 1)

        # Make array of timestamp ints
        # TODO: Doesn't support multiple fields
        time = ((fields.index.to_datetime().values.astype(int) /
                 precision_factor).astype(int).astype(str))

        # If tag columns exist, make an array of formatted tag keys and values
        if tags is not None:
            if isinstance(tags, pd.Series):
                tag_df = pd.DataFrame(list(zip(tags)), columns=[tag_names])
            elif isinstance(tags, list):
                tag_df = pd.DataFrame(list(zip(*tags)), columns=tag_names)
            else:
                print(type(tags))
                raise ValueError
            tag_df = self._stringify_dataframe(
                tag_df, numeric_precision, datatype='tag')
            tags = (',' + (
                (tag_df.columns.values + '=').tolist() + tag_df)).sum(axis=1)
            del tag_df

        else:
            tags = ''

        # Make an array of formatted field keys and values
        if isinstance(fields, pd.Series):
            field_df = pd.DataFrame(list(zip(fields)), columns=[field_names])
        elif isinstance(fields, list):
            field_df = pd.DataFrame(list(zip(*fields)), columns=field_names)
        field_df = self._stringify_dataframe(
            field_df, numeric_precision, datatype='field')
        field_df = (field_df.columns.values + '=').tolist() + field_df
        field_df[field_df.columns[1:]] = ',' + field_df[field_df.columns[1:]]
        fields = field_df.sum(axis=1)
        del field_df

        # Add any global tags to formatted tag strings
        if global_tags:
            global_tags = ','.join(['='.join([tag, global_tags[tag]])
                                    for tag in global_tags])
            if tags is not None:
                tags = tags + ',' + global_tags
            else:
                tags = ',' + global_tags

        # Generate line protocol string
        points = (measurement + tags + ' ' + fields + ' ' + time).tolist()
        return points

    def _convert_dataframe_to_lines(self,
                                    dataframe,
                                    measurement,
                                    field_columns=[],
                                    tag_columns=[],
                                    global_tags={},
                                    time_precision=None,
                                    numeric_precision=None):

        if not isinstance(dataframe, pd.DataFrame):
            raise TypeError('Must be DataFrame, but type was: {0}.'
                            .format(type(dataframe)))
        if not (isinstance(dataframe.index, pd.tseries.period.PeriodIndex) or
                isinstance(dataframe.index, pd.tseries.index.DatetimeIndex)):
            raise TypeError('Must be DataFrame with DatetimeIndex or \
                            PeriodIndex.')

        # Create a Series of columns for easier indexing
        column_series = pd.Series(dataframe.columns)

        if field_columns is None:
            field_columns = []
        if tag_columns is None:
            tag_columns = []

        # Make sure field_columns and tag_columns are lists
        field_columns = list(field_columns) if list(field_columns) else []
        tag_columns = list(tag_columns) if list(tag_columns) else []

        # If field columns but no tag columns, assume rest of columns are tags
        if field_columns and (not tag_columns):
            tag_columns = list(column_series[~column_series.isin(
                field_columns)])

        # If no field columns, assume non-tag columns are fields
        if not field_columns:
            field_columns = list(column_series[~column_series.isin(
                tag_columns)])

        precision_factor = {
            "n": 1,
            "u": 1e3,
            "ms": 1e6,
            "s": 1e9,
            "m": 1e9 * 60,
            "h": 1e9 * 3600,
        }.get(time_precision, 1)

        # Make array of timestamp ints
        time = ((dataframe.index.to_datetime().values.astype(int) /
                 precision_factor).astype(int).astype(str))

        # If tag columns exist, make an array of formatted tag keys and values
        if tag_columns:
            tag_df = dataframe[tag_columns]
            tag_df = self._stringify_dataframe(
                tag_df, numeric_precision, datatype='tag')
            tags = (',' + (
                (tag_df.columns.values + '=').tolist() + tag_df)).sum(axis=1)
            del tag_df

        else:
            tags = ''

        # Make an array of formatted field keys and values
        field_df = dataframe[field_columns]
        field_df = self._stringify_dataframe(
            field_df, numeric_precision, datatype='field')
        field_df = (field_df.columns.values + '=').tolist() + field_df
        field_df[field_df.columns[1:]] = ',' + field_df[field_df.columns[1:]]
        fields = field_df.sum(axis=1)
        del field_df

        # Add any global tags to formatted tag strings
        if global_tags:
            global_tags = ','.join(['='.join([tag, global_tags[tag]])
                                    for tag in global_tags])
            if tag_columns:
                tags = tags + ',' + global_tags
            else:
                tags = ',' + global_tags

        # Generate line protocol string
        points = (measurement + tags + ' ' + fields + ' ' + time).tolist()
        return points

    def write_points(self, line_series):
        return self.client.write_points(line_series, protocol='line')

    def run(self, serving_dict):
        lines = self._convert_series_to_lines(**serving_dict)
        return self.write_points(lines)
