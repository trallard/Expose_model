{
    'service_metadata': {
        'service_name': 'iris',
        'service_version': '0.1',
    },

    'dataset_loader_train': {
        '__factory__': 'expose.R.DatasetLoader',
        'scriptname': 'iris.R',
        'funcname': 'dataset',
    },

    'dataset_loader_test': {
        '__factory__': 'expose.R.DatasetLoader',
        'scriptname': 'iris.R',
        'funcname': 'dataset',
    },

    'model': {
        '__factory__': 'expose.R.ClassificationModel',
        'scriptname': 'iris.R',
        'funcname': 'train.randomForest',
        'encode_labels': True,
    },

    'model_persister': {
        '__factory__': 'expose.persistence.CachedUpdatePersister',
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
}
