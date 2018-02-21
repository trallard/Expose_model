#model_expose

this package allows to set up analytics services as web apps.

As this is it provides generic implementations for models in data science such
as:
data set loading, model training with parameter search, web services, and
persistence capabilities.

The already developed components are tied to your components via a config file:

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
Clone the repository and from `Expose_test` run the following command on the terminal
```
$ conda env create -f expose.yml
```
Activate the environment `source activate expose`
Once there you need to install the package like so `pip install .`

You'll then need to set a 
