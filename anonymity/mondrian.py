'''
'''

import pandas as pd


def is_k_anonymous(partition, k=4):
    '''
    '''
    if len(partition) < k:
        return False
    return True


class MondrianAnonymizer:
    def __init__(self, is_valid_func, **kwargs):
        '''
        '''
        self.is_valid_func = lambda x: is_valid_func(x, **kwargs)


    @staticmethod
    def _agg_categorical_column(s):
        '''
        '''    
        return ','.join(sorted(map(str, s.unique())))

    @staticmethod
    def _agg_numerical_column(s):
        '''
        '''
        s_unique = s.unique()
        if len(s_unique) == 1:
            return s_unique[0]
        else:
            return f'{s.min()}-{s.max()}'

    @staticmethod
    def _get_spans(df, features, categorical, partition):
        '''
        '''
        spans = {}
        for col in features:
            if col in categorical:
                span = len(df[col][partition].unique())
            else:
                span = df[col][partition].max() - df[col][partition].min()
            spans[col] = span
        return spans

    @staticmethod
    def _split(df, categorical, col, partition):
        '''
        '''
        dfp = df[col][partition]
        if col in categorical:
            values = dfp.unique()
            lv = set(values[:len(values)//2])
            rv = set(values[len(values)//2:])
            return dfp.index[dfp.isin(lv)], dfp.index[dfp.isin(rv)]
        else:        
            median = dfp.median()
            dfl = dfp.index[dfp < median]
            dfr = dfp.index[dfp >= median]
            return (dfl, dfr)


    def _partition_dataset(self, df, features, categorical, is_valid_func):
        '''
        '''
        finished_partitions = []
        partitions = [df.index]
        while partitions:
            partition = partitions.pop(0)
            spans = self._get_spans(df, features, categorical, partition)
            for col, span in sorted(spans.items(), key=lambda x:-x[1]):
                lp, rp = self._split(df, categorical, col, partition)
                if not is_valid_func(lp) or not is_valid_func(rp):
                    continue
                partitions.extend((lp, rp))
                break
            else:
                finished_partitions.append(partition)
        return finished_partitions



    def anonymize(self, df, features, categorical, sensitive):
        '''
        '''
        finished_partitions = self._partition_dataset(df, features, categorical, self.is_valid_func)

        res = []
        for partition in finished_partitions:
            dfx = df.loc[partition, features].copy()
            for col in features:
                aggfunc = self._agg_categorical_column if col in categorical else self._agg_numerical_column
                dfx[col] = aggfunc(dfx[col])
            res.append(dfx)

        return pd.concat([pd.concat(res).sort_index(), df[sensitive]], axis=1)