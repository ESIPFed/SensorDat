import json
import numpy as np
import pandas as pd
import re

import influxdb_driver

def constant(value, series):
    if isinstance(series, pd.Series):
        return pd.Series(value, index=series.index)
    elif isinstance(series, pd.Index):
        return pd.Series(value, index=series)
    else:
        raise ValueError('Series must be a pandas Series or Index')

class Cookbook():
    def __init__(self, cookbook_path):

        self._registry = {}

        self._comparisons = {'>' : np.greater,
                             '<' : np.less,
                             '>=' : np.greater_equal,
                             '<=' : np.less_equal,
                             '==' : np.equal,
                             '!=' : np.not_equal,
                             'in' : np.isin}

        self._logicals = {'and' : np.logical_and.reduce,
                          'or' : np.logical_or.reduce,
                          'not' : np.logical_not.reduce,
                          'xor' : np.logical_xor.reduce}

        self._transforms = {'return' : lambda x : x,
                            '+' : np.add,
                            '-' : np.subtract,
                            '*' : np.multiply,
                            '/' : np.divide,
                            '//' : np.floor_divide,
                            '%' : np.mod,
                            '**' : np.power,
                            'add' : np.add,
                            'subtract' : np.subtract,
                            'multiply' : np.multiply,
                            'divide' : np.divide,
                            'logaddexp' : np.logaddexp,
                            'logaddexp2' : np.logaddexp2,
                            'true_divide' : np.true_divide,
                            'floor_divide' : np.floor_divide,
                            'negative' : np.negative,
                            'positive' : np.positive,
                            'power' : np.power,
                            'remainder' : np.remainder,
                            'mod' : np.mod,
                            'fmod' : np.fmod,
                            'divmod' : np.divmod,
                            'absolute' : np.absolute,
                            'fabs' : np.fabs,
                            'rint' : np.rint,
                            'sign' : np.sign,
                            'heaviside' : np.heaviside,
                            'conj' : np.conj,
                            'exp' : np.exp,
                            'exp2' : np.exp2,
                            'log' : np.log,
                            'log2' : np.log2,
                            'log10' : np.log10,
                            'expm1' : np.expm1,
                            'log1p' : np.log1p,
                            'sqrt' : np.sqrt,
                            'square' : np.square,
                            'cbrt' : np.cbrt,
                            'reciprocal' : np.reciprocal,
                            'sin' : np.sin,
                            'cos' : np.cos,
                            'tan' : np.tan,
                            'arcsin' : np.arcsin,
                            'arccos' : np.arccos,
                            'arctan' : np.arctan,
                            'arctan2' : np.arctan2,
                            'hypot' : np.hypot,
                            'sinh' : np.sinh,
                            'cosh' : np.cosh,
                            'tanh' : np.tanh,
                            'arcsinh' : np.arcsinh,
                            'arccosh' : np.arccosh,
                            'arctanh' : np.arctanh,
                            'deg2rad' : np.deg2rad,
                            'rad2deg' : np.rad2deg,
                            'bitwise_and' : np.bitwise_and,
                            'bitwise_or' : np.bitwise_or,
                            'bitwise_xor' : np.bitwise_xor,
                            'invert' : np.invert,
                            'left_shift' : np.left_shift,
                            'right_shift' : np.right_shift,
                            'greater' : np.greater,
                            'greater_equal' : np.greater_equal,
                            'less' : np.less,
                            'less_equal' : np.less_equal,
                            'not_equal' : np.not_equal,
                            'equal' : np.equal,
                            'logical_and' : np.logical_and,
                            'logical_or' : np.logical_or,
                            'logical_xor' : np.logical_xor,
                            'logical_not' : np.logical_not,
                            'maximum' : np.maximum,
                            'minimum' : np.minimum,
                            'fmax' : np.fmax,
                            'fmin' : np.fmin,
                            'isfinite' : np.isfinite,
                            'isinf' : np.isinf,
                            'isnan' : np.isnan,
                            'isnat' : np.isnat,
                            'signbit' : np.signbit,
                            'copysign' : np.copysign,
                            'nextafter' : np.nextafter,
                            'spacing' : np.spacing,
                            'modf' : np.modf,
                            'ldexp' : np.ldexp,
                            'frexp' : np.frexp,
                            'fmod' : np.fmod,
                            'floor' : np.floor,
                            'ceil' : np.ceil,
                            'trunc' : np.trunc,
                            'diff' : pd.Series.diff,
                            'replace' : pd.Series.replace,
                            'constant' : constant,
                            'fillna' : pd.Series.fillna,
                            'mask' : pd.Series.mask,
                            'where' : pd.Series.where
                        }

        self._aggregators = {'sum' : np.sum,
                             'prod' : np.prod,
                             'mean' : np.mean,
                             'std' : np.std,
                             'var' : np.var,
                             'min' : np.min,
                             'max' : np.max,
                             'argmin' : np.argmin,
                             'argmax' : np.argmax,
                             'median' : np.median,
                             'percentile' : np.percentile,
                             'nansum' : np.nansum,
                             'nanprod' : np.nanprod,
                             'nanmean' : np.nanmean,
                             'nanstd' : np.nanstd,
                             'nanvar' : np.nanvar,
                             'nanmin' : np.nanmin,
                             'nanmax' : np.nanmax,
                             'nanargmin' : np.nanargmin,
                             'nanargmax' : np.nanargmax,
                             'nanmedian' : np.nanmedian,
                             'nanpercentile' : np.nanpercentile,
                             'any' : np.any,
                             'all' : np.all}

        self.input_drivers = {'influxdb' : influxdb_driver.InfluxDBInput}
        self.output_drivers = {'influxdb' : influxdb_driver.InfluxDBOutput}

        self.year_re = re.compile('\d\d\d\d')

        self.ingredient_types = {}
        self.annotations = {}

        self.recipe_types = {'query' : self.parse_query,
                             'drop' : self.parse_drop,
                             'join' : self.parse_join,
                             'transformation' : self.parse_transformation,
                             'annotation' : self.parse_annotation,
                             'aggregation' : self.parse_aggregation,
                             'delete' : self.parse_delete}

        with open(cookbook_path) as cookbook:
            self.cookbook = json.load(cookbook)

    def parse_query(self, query_dict):
        _select = query_dict['select']
        select = self.parse_datasource(_select)
        if 'where' in query_dict:
            _where = query_dict['where']
            where = self.parse_where(_where)
            obj = select[where]
        else:
            obj = select
        _as = query_dict['@as']
        setattr(self, _as, obj)

    def parse_drop(self, query_dict):
        _select = query_dict['select']
        select = self.parse_datasource(_select)
        if 'where' in query_dict:
            _where = query_dict['where']
            where = self.parse_where(_where)
            obj = select[~where]
        else:
            obj = select
        _as = query_dict['@as']
        setattr(self, _as, obj)

    def parse_transformation(self, transformation_dict):
        if 'where' in transformation_dict:
            _where = transformation_dict['where']
            where = self.parse_where(_where)
            _do = transformation_dict['do']
            do_result = self.parse_operation(_do, op_type='transformation')
            if not isinstance(do_result, pd.Series):
                do_result = pd.Series(do_result, index=where.index)
            if 'else' in transformation_dict:
                _else = transformation_dict['else']
                else_result = self.parse_operation(_else, op_type='transformation')
            else:
                else_result = np.nan
            obj = do_result.where(cond=where, other=else_result)
        else:
            _do = transformation_dict['do']
            do_result = self.parse_operation(_do, op_type='transformation')
            obj = do_result
        _as = transformation_dict['@as']
        setattr(self, _as, obj)

    def parse_operation(self, transform_dict, op_type):
        operation = transform_dict.pop('@type')
        if op_type == 'transformation':
            transform = self._transforms[operation]
        elif op_type == 'aggregation':
            transform = self._aggregators[operation]
        else:
            raise ValueError
        args = transform_dict['args']
        kwargs = transform_dict.setdefault('kwargs', {})
        out_args = []
        # TODO: Assumes kwargs aren't nested
        out_kwargs = kwargs
        if not isinstance(args, list):
            args = [args]
        for arg in args:
            if isinstance(arg, dict):
                if '@type' in arg:
                    arg = self.parse_operation(arg, op_type)
            elif isinstance(arg, str):
                baseobj = arg.split('.')[0]
                if hasattr(self, baseobj):
                    arg = self.parse_datasource(arg)
                elif re.search(self.year_re, arg):
                    try:
                        arg = pd.to_datetime(arg).asm8
                    except:
                        pass
            out_args.append(arg)
        return transform(*out_args, **out_kwargs)

    def parse_aggregation(self, aggregation_dict):
        _do = aggregation_dict['do']
        obj = self.parse_operation(_do, op_type='aggregation')
        _as = aggregation_dict['@as']
        setattr(self, _as, obj)

    def parse_where(self, where_dict):
        (key, values), = where_dict.items()
        if key in self._logicals:
            return self.parse_logical({key : values})
        elif key in self._comparisons:
            return self.parse_binary_comparison({key : values})

    def parse_logical(self, logical_dict):
        assert (len(logical_dict) == 1)
        (key, values), = logical_dict.items()
        args = []
        assert isinstance(values, list)
        for value in values:
            assert isinstance(value, dict)
            for subkey, subvalue in value.items():
                # Avoid set lookups
                if subkey in self._logicals:
                    result = self.parse_logical(value)
                    args.append(result)
                elif subkey in self._comparisons:
                    result = self.parse_binary_comparison(value)
                    args.append(result)
        logical_result = self._logicals[key](args)
        return logical_result

    def parse_binary_comparison(self, comparison_dict):
        # Kind of wonky
        assert (len(comparison_dict) == 1)
        (key, values), = comparison_dict.items()
        args = []
        assert (len(values) == 2)
        for arg in values:
            if isinstance(arg, str):
                baseobj = arg.split('.')[0]
                if hasattr(self, baseobj):
                    arg = self.parse_datasource(arg)
                elif re.search(self.year_re, arg):
                    try:
                        arg = pd.to_datetime(arg).asm8
                    except:
                        pass
            args.append(arg)
        comparison_result = self._comparisons[key](*args)
        return comparison_result

    def parse_delete(self, delete_dict):
        _select = delete_dict['select']
        for arg in _select:
            delattr(self, arg)

    def parse_join(self, join_dict):
        obj_names = join_dict.pop('select')
        objs = [getattr(self, name) for name in obj_names]
        _as = join_dict.pop('@as')
        obj = pd.concat(objs, **join_dict)
        setattr(self, _as, obj)

    def parse_datasource(self, name):
        arg_list = name.split('.')
        obj = self
        for arg in arg_list:
            obj = getattr(obj, arg)
        return obj

    def parse_annotation(self, annotation_dict):
        # TODO: Note that if index changes, annotation will be misaligned
        _where = annotation_dict.pop('where')
        _name = annotation_dict.pop('name')
        _on = annotation_dict.pop('on')
        where = self.parse_where(_where)
        result_d = {**annotation_dict}
        result_d.update({'where' : where})
        if not _on in self.annotations:
            self.annotations.update({_on : {}})
        self.annotations[_on].update({_name : {}})
        self.annotations[_on][_name].update(result_d)

    def set_datasources(self):
        datasources = self.cookbook['sources']
        for datasource in datasources:
            datasource_type = datasource.pop('@type')
            name = datasource['name']
            path = datasource['url']
            with open(path) as infile:
                driver_dict = json.load(infile)
            driver_context = driver_dict.pop('@context')
            driver_type = driver_dict.pop('@type')
            driver = self.input_drivers[driver_type](driver_dict)
            setattr(self, name, driver)

    def set_destinations(self):
        destinations = self.cookbook['destinations']
        for destination in destinations:
            destination_type = destination.pop('@type')
            name = destination['name']
            path = destination['url']
            with open(path) as infile:
                driver_dict = json.load(infile)
            driver_context = driver_dict.pop('@context')
            driver_type = driver_dict.pop('@type')
            driver = self.output_drivers[driver_type](driver_dict)
            setattr(self, name, driver)

    def prepare_ingredients(self):
        ingredientlist = self.cookbook['ingredients']
        for ingredient in ingredientlist:
            driver_type = ingredient.pop('@type')
            driver_name = ingredient.pop('source')
            _as = ingredient.pop('@as')
            datasource = getattr(self, driver_name)
            data = datasource.run(ingredient)
            setattr(self, _as, data)

    def prepare_recipe(self):
        recipelist = self.cookbook['recipe']
        for recipe in recipelist:
            recipe_type = recipe.pop('@type')
            self.recipe_types[recipe_type](recipe)

    def prepare_serving(self):
        servinglist = self.cookbook['servings']
        for serving in servinglist:
            driver_type = serving.pop('@type')
            driver_name = serving.pop('destination')
            dataclient = getattr(self, driver_name)
            # This needs to be moved into the driver
            if isinstance(serving['fields'], list):
                serving['fields'] = [getattr(self, field) for field in serving['fields']]
            elif isinstance(serving['fields'], str):
                serving['fields'] = getattr(self, serving['fields'])
            if 'tags' in serving:
                if isinstance(serving['tags'], list):
                    serving['tags'] = [getattr(self, tag) for tag in serving['tags']]
                elif isinstance(serving['tags'], str):
                    serving['tags'] = getattr(self, serving['tags'])
            data = dataclient.run(serving)

    def run(self):
        self.set_datasources()
        self.set_destinations()
        self.prepare_ingredients()
        self.prepare_recipe()
        self.prepare_serving()
