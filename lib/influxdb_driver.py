import influxdb
import pandas as pd

class InfluxDBDriver():
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
