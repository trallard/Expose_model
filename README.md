# model_expose
The model expose package allows to set up analytics services as web apps.

As this is it provides generic implementations for models in data science/analytics such
as:
data set loading, model training with parameter search, web services, and
persistence capabilities.

This is intended to be able to serve as a 'generic' package allowing to
connect the package modules with specific models and data sets via a
[config.py file](./sample_models/python/config.py)

```python
{
    'service_metadata': {
        'service_name': 'iris',
        'service_version': '0.1',
    },

    'dataset_loader_train': {
        '__factory__': 'expose.dataset.Table',
        'path': 'iris.data',
        'names': [
            'sepal length',
            'sepal width',
            'petal length',
            'petal width',
            'species',
        ],
        'target_column': 'species',
        'sep': ',',
        'nrows': 100,
    },

    'dataset_loader_test': {
        '__factory__': 'expose.dataset.Table',
        'path': 'iris.data',
        'names': [
            'sepal length',
            'sepal width',
            'petal length',
            'petal width',
            'species',
        ],
        'target_column': 'species',
        'sep': ',',
        'skiprows': 100,
    },

    'model': {
        '__factory__': 'sklearn.linear_model.LogisticRegression',
        'C': 0.3,
    },

    'grid_search': {
        'param_grid': {
            'C': [0.1, 0.3, 1.0],
        },
        'verbose': 4,
        'n_jobs': -1,
    },

    'model_persister': {
        '__factory__': 'expose.persistence.CachedUpdatePersister',
        'update_cache_rrule': {'freq': 'HOURLY'},
        'impl': {
            '__factory__': 'expose.persistence.Database',
            'url': 'sqlite:///iris-model.db',
        },
    },

    'predict_service': {
        '__factory__': 'expose.server.PredictService',
        'mapping': [
            ('sepal length', 'float'),
            ('sepal width', 'float'),
            ('petal length', 'float'),
            ('petal width', 'float'),
        ],
    },

    'alive': {
        'process_store_required': ('model',),
    },
}

```

### Usage
**Note**: since the package is still in alpha stage it has not been
made available on PyPi or similar. Thus installation will have to be
made from source.

The first step to use the app is to create an anaconda environment.
Thus assuming you have a working installation of Anaconda on your computer
you can go to the `Expose_model` directory and create an anaconda environment from the command line
like so:
```
$ conda env create -f expose.yml
```
After creating the environment you'll need to activate it by invoking: `source activate expose` from the shell.

To install the package within the environment you can then do `python setup.py`
