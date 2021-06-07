'''
'''
from collections import defaultdict
import pandas as pd

def is_k_anonymous(partition, k=4):
    '''
    Returns True if the provided partition has a size greater or equal than k

    Parameters
    ----------
    partition: list (or Index)
        indexes of the dataframe which describe the current partition (anonymization process)
    k: int
        minimal size of the partition
    '''
    return len(partition) >= k

def _handle_metadata(d_metadata):
    '''
    Helper function which outputs 4 list out of the dictionary of metadata.
    The metadata dictionary is built so that for each variable there is a dictionary of binary descriptor.
    This means:

    {key: {'is_sensitive':, 'is_categorical':, 'prevent_generalization':}}
    
    There are a few rules:
    * If a key is missing, it defaults to False.
    * A variable is either sensitive, prevented from generalizing or a feature.
    * If neither is_sensitive or prevent_generalization are True, it means the variable is a feature.
    * Only features may be categorical.

    Parameters
    ----------
    d_metadata: dict
        describes the variables
    
    Returns
    -------
    features: list
        list of all features subject to generalization
    no_agg_features: list
        list of all features which are not subject to generalization
    categorical: list
        subset of features which are categorical variables, this means the others will be considered as continuous (no ordinal and what not)
    sensitive: list
        list of all sensitive features (distinct from features and no_agg_features)
    '''
    features, no_agg_features, categorical, sensitive = \
        list(), list(), list(), list()

    for feature, d in d_metadata.items():
        d = defaultdict(bool, d)
        assert d['is_sensitive'] + d['is_feature'] + d['prevent_generalization'] <= 1
        assert d['is_categorical'] == d['is_feature']

        if d['is_sensitive']:
            sensitive.append(feature)
        elif d['prevent_generalization']:
            no_agg_features.append(feature)
        else:
            features.append(feature)
            if d['is_categorical']:
                categorical.append(feature)
    return sorted(features), sorted(no_agg_features),\
        sorted(categorical), sorted(sensitive)

class MondrianAnonymizer:
    '''
    Anonymizer class based on the Mondrian top down algorithm.
    Supports K-anonymisation and L-diversity. The l parameter provided will behave so that all sensitive variables have
    at least l distinct values for each group.

    Attributes
    ----------
    k: int
        Minimal partition size

    l: int
        Minimal number of distinct sensitive values for each partition. The expected behavior is that ALL sensitive variables have
        at least l distinct values for each group.

    df: pd.DataFrame
        The dataframe provided to the anonymize function. Before call this function, defaults to None
    
    features: list(str)
        list of all features subject to generalization

    no_agg_features: list
        list of all features which are not subject to generalization

    categorical: list
        subset of features which are categorical variables, this means the others will be considered as continuous (no ordinal and what not)
    
    sensitive: list
        list of all sensitive features (distinct from features and no_agg_features)


    Methods
    -------
    anonymize(df, d_metadata)
        Anonymizes the provided dataframe according to the k and l parameters provided to the anonymizer.

    get_individual(df_anonymized, s_individual)
        Finds all the records in df_anonymized which corresponds to the provided individual (using only features and prevent_generalization features)

    References
    ----------
    ..[1] K. LeFevre, D. J. DeWitt and R. Ramakrishnan, "Mondrian Multidimensional K-Anonymity," 22nd International Conference on Data Engineering (ICDE'06), 2006, pp. 25-25, doi: 10.1109/ICDE.2006.101.
    '''
    def __init__(self, k=4, l=None):
        self.k = k
        self.l = l
        self.df = None
        self.features = None
        self.no_agg_features = None
        self.categorical = None
        self.sensitive = None

    @staticmethod
    def is_valid(partition, df_sensitive, k, l):
        '''
        '''
        if (df_sensitive is None) or l is None:
            flag = True
        else:
            flag = (df_sensitive.loc[partition].apply(lambda x: x.nunique()) >= l).all()
            
        return is_k_anonymous(partition, k) and flag 

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

    def _get_spans(self, df, partition):
        '''
        '''
        spans = {}
        for col in self.features:
            if col in self.categorical:
                span = df[col][partition].nunique()
            else:
                span = df[col][partition].max() - df[col][partition].min()
            spans[col] = span
        return spans

    def _split(self, df, col, partition):
        '''
        '''
        dfp = df[col][partition]
        if col in self.categorical:
            values = dfp.unique()
            lv = set(values[:len(values)//2])
            rv = set(values[len(values)//2:])
            return dfp.index[dfp.isin(lv)], dfp.index[dfp.isin(rv)]
        else:        
            median = dfp.median()
            dfl = dfp.index[dfp < median]
            dfr = dfp.index[dfp >= median]
            return (dfl, dfr)

    def _partition_dataset(self, df):
        '''
        '''
        finished_partitions = []
        partitions = [df.index]
        while partitions:
            partition = partitions.pop(0)
            spans = self._get_spans(df, partition)
            for col, span in sorted(spans.items(), reverse=True):
                lp, rp = self._split(df, col, partition)

                if not self.is_valid(lp, df.loc[lp, self.sensitive], self.k, self.l) or \
                    not self.is_valid(rp, df.loc[rp, self.sensitive], self.k, self.l):
                    continue
                partitions.extend((lp, rp))
                break
            else:
                finished_partitions.append(partition)
        return finished_partitions



    def _anonymize(self, df):
        '''
        '''
        finished_partitions = self._partition_dataset(df)

        res = []
        for partition in finished_partitions:
            dfx = df.loc[partition, self.features].copy()
            for col in self.features:
                aggfunc = self._agg_categorical_column if col in self.categorical else self._agg_numerical_column
                dfx[col] = aggfunc(dfx[col])
            res.append(dfx)

        return pd.concat([pd.concat(res).sort_index(), df[self.sensitive]], axis=1)

    def anonymize(self, df, d_metadata):
        '''
        Anonymizes the provided dataframe according to the k and l parameters provided to the anonymizer.
        The metadata dictionary is built so that for each variable there is a dictionary of binary descriptor.

        This means:

        {key: {'is_sensitive':, 'is_categorical':, 'prevent_generalization':}}

        There are a few rules:
        * If a key is missing, it defaults to False.
        * A variable is either sensitive, prevented from generalizing or a feature.
        * If neither is_sensitive or prevent_generalization are True, it means the variable is a feature.
        * Only features may be categorical.

        Parameters
        ----------
        df: pd.DataFrame
            input DataFrame
        
        d_metadata: dict
            describes the variables

        Returns
        -------
        df_anonymize: pd.DataFrame
            anonymized DataFrame

        '''
        self.df = df
        self.d_metadata = d_metadata
        self.features, self.no_agg_features, self.categorical, self.sensitive = \
            _handle_metadata(self.d_metadata)

        res = []
        for _, dfx in self.df.groupby(self.no_agg_features):
            dfy = self._anonymize(dfx)
            dfy[self.no_agg_features] = dfx[self.no_agg_features]
            res.append(dfy)
        return pd.concat(res).loc[self.df.index, self.features + self.no_agg_features + self.sensitive]

    def get_individual(self, df_anonymized, s_individual):
        '''
        Finds all the records in df_anonymized which corresponds to the provided
        individual (using only features and prevent_generalization features).

        Parameters
        ----------
        df_anonymized: pd.DataFrame
            Anonymized DataFrame containing the searched individual and others

        s_individual: pd.Series
            Series describing the searched individual. It must contain at least the features and 
            prevent_generalization features used for the anonymization
        '''
        q = ' and '.join([f'{col} == {s_individual[col]}' for col in self.no_agg_features])
        dfx = df_anonymized.query(q)
        res_idxes = set()
        for col in self.features:
            idxes = []
            for i, val in enumerate(dfx[col].values):
                x = s_individual[col]
                val = str(val)
                if '-' in val:
                    m, M = map(int, val.split('-'))
                    if (m <= x) and (x < M):
                        idxes.append(i)
                elif ',' in val:
                    if x in map(int, val.split(',')):
                        idxes.append(i)
                else:
                    if x == int(val):
                        idxes.append(i)
        
            if len(res_idxes) == 0:
                res_idxes = set(idxes)
            else:
                res_idxes &= set(idxes) 
        
        return dfx.iloc[sorted(res_idxes)]
