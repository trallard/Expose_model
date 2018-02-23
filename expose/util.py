#!/usr/bin/env python
"""Number of utilities used through the various modules
"""

from collections import UserDict
from contextlib import contextmanager
from datetime import datetime
from functools import partial
from functools import wraps
import logging
from logging.config import dictConfig
from importlib import import_module
from inspect import signature
from inspect import getcallargs
import os
import sys
from threading import Thread
from time import sleep
from time import time

import dateutil.parser
import dateutil.rrule
from docopt import docopt
import psutil

from . import __version__

logger = logging.getLogger('expose')


expose_CONFIG_ERROR = """
    Did you set the expose_CONFIG environment variable?
    If you did not make sure to add it by typing
    export expose_CONFIG=config.py from the shell
"""


def resolve_dotted_name(dotted_name):
    """ Resolves the names of the modules being
    requested
    Args:
        dotted_name: module name
    Returns:
        attr: a string corresponding  to the
        module name
    """
    
    if ':' in dotted_name:
        module, name = dotted_name.split(':')
    else:
        module, name = dotted_name.rsplit('.', 1)

    attr = import_module(module)
    for name in name.split('.'):
        attr = getattr(attr, name)

    return attr


def create_component(specification):
    specification = specification.copy()
    factory_dotted_name = specification.pop('__factory__')
    factory = resolve_dotted_name(factory_dotted_name)
    return factory(**specification)


class Config(dict):
    """A dictionary containing the app configuration.
    It provides error messages in case of KeyErrors
    """
    initialized = False

    def __getitem__(self, name):
        try:
            return super(Config, self).__getitem__(name)
        except KeyError:
            raise KeyError(
                "The required key '{}' does not exist in "
                "configuration. {}".format(name, expose_CONFIG_ERROR))

_config = Config()


def get_config(**extra):
    """Loads the configuration given to initialize
    the app
    """
    if not _config.initialized:
        _config.update(extra)
        _config.initialized = True
        fnames = os.environ.get('expose_CONFIG')
        if fnames is not None:
            fnames = [fname.strip() for fname in fnames.split(',')]
            sys.path.insert(0, os.path.dirname(fnames[0]))
            for fname in fnames:
                with open(fname) as f:
                    _config.update(
                        eval(f.read(), {
                            'environ': os.environ,
                            'here': os.path.abspath(os.path.dirname(fname)),
                            })
                        )
            _initialize_config(_config)

    return _config


def initialize_config(**extra):
    """Initializes the config for the app
    """
    if _config.initialized:
        raise RuntimeError("This was previously initialised. Skipping.")
    return get_config(**extra)


def _initialize_config_recursive(props):
    rv = []
    if isinstance(props, dict):
        for key, value in tuple(props.items()):
            if isinstance(value, dict):
                rv.extend(_initialize_config_recursive(value))
                if '__factory__' in value:
                    props[key] = create_component(value)
                    rv.append(props[key])
            elif isinstance(value, (list, tuple)):
                rv.extend(_initialize_config_recursive(value))
    elif isinstance(props, (list, tuple)):
        for i, item in enumerate(props):
            if isinstance(item, dict):
                rv.extend(_initialize_config_recursive(item))
                if '__factory__' in item:
                    props[i] = create_component(item)
                    rv.append(props[i])
            elif isinstance(item, (list, tuple)):
                rv.extend(_initialize_config_recursive(item))
    return rv


def _initialize_config(config):
    components = []

    if 'logging' in config:
        dictConfig(config['logging'])
    else:
        logging.basicConfig(level=logging.DEBUG)

    components = _initialize_config_recursive(config)
    for component in components:
        if hasattr(component, 'initialize_component'):
            component.initialize_component(config)

    return config


def apply_kwargs(func, **kwargs):
    """Call *func* with kwargs
    Note this only takes the ones accepted by the function
    """
    new_kwargs = {}
    params = signature(func).parameters
    for param_name in params.keys():
        if param_name in kwargs:
            new_kwargs[param_name] = kwargs[param_name]
    return func(**new_kwargs)


def args_from_config(func):
    """Decorator that injects parameters from the configuration.
    """
    func_args = signature(func).parameters

    @wraps(func)
    def wrapper(*args, **kwargs):
        config = get_config()
        for i, argname in enumerate(func_args):
            if len(args) > i or argname in kwargs:
                continue
            elif argname in config:
                kwargs[argname] = config[argname]
        try:
            getcallargs(func, *args, **kwargs)
        except TypeError as exc:
            msg = "{}\n{}".format(exc.args[0], expose_CONFIG_ERROR)
            exc.args = (msg,)
            raise exc
        return func(*args, **kwargs)

    wrapper.__wrapped__ = func
    return wrapper


@contextmanager
def timer(log=None, message=None):
    if log is not None:
        log("{}...".format(message))

    info = {}
    t0 = time()
    yield info

    info['elapsed'] = time() - t0
    if log is not None:
        log("{} done in {:.3f} sec.".format(message, info['elapsed']))


@contextmanager
def session_scope(session):
    """Provide a transactional scope around a series of operations."""
    try:
        yield session
        session.commit()
    except:
        session.rollback()
        raise
    finally:
        session.close()


class ProcessStore(UserDict):
    def __init__(self, *args, **kwargs):
        self.mtime = {}
        super(ProcessStore, self).__init__(*args, **kwargs)

    def __setitem__(self, key, item):
        super(ProcessStore, self).__setitem__(key, item)
        self.mtime[key] = datetime.now()

    def __getitem__(self, key):
        return super(ProcessStore, self).__getitem__(key)

    def __delitem__(self, key):
        super(ProcessStore, self).__delitem__(key)
        del self.mtime[key]


process_store = ProcessStore()


class RruleThread(Thread):
    """Calls a given function in intervals defined by given recurrence
    rules (from `datetuil.rrule`).
    """
    def __init__(self, func, rrule, sleep_between_checks=60):
        """
        Args:
            callable func: The function that I will call periodically.

            rrule rrule: The :class:`dateutil.rrule.rrule` recurrence rule that
          defines when I will do the calls.  See the `python-dateutil
          docs <https://labix.org/python-dateutil>`_ for details on
          how to define rrules.

          For convenience, I will also accept a dict instead of a
          `rrule` instance, in which case I will instantiate an rrule
          using the dict contents as keyword parameters.

        sleep_between_checks: Number of seconds to sleep before
        checking if function *func* needs to be run again.
        """
        super(RruleThread, self).__init__(daemon=True)
        if isinstance(rrule, dict):
            rrule = self._rrule_from_dict(rrule)
        self.func = func
        self.rrule = rrule
        self.sleep_between_checks = sleep_between_checks
        self.last_execution = datetime.now()
        self.alive = True

    @classmethod
    def _rrule_from_dict(cls, rrule):
        kwargs = rrule.copy()
        for key, value in rrule.items():
            # Allow constants in datetutil.rrule to be passed as strings
            if isinstance(value, str) and hasattr(dateutil.rrule, value):
                kwargs[key] = getattr(dateutil.rrule, value)

        dstart = kwargs.get('dtstart')
        if isinstance(dstart, str):
            kwargs['dtstart'] = dateutil.parser.parse(dstart)
        return dateutil.rrule.rrule(**kwargs)

    def run(self):
        while self.alive:
            now = datetime.now()
            if not self.rrule.between(self.last_execution, now):
                sleep(self.sleep_between_checks)
                continue

            self.last_execution = now

            try:
                self.func()
            except:
                logger.exception(
                    "Failed to call {}".format(self.func.__name__))


def memory_usage_psutil():
    """Return the current process memory usage in MB.
    """
    process = psutil.Process(os.getpid())
    mem = process.memory_info()[0] / float(2 ** 20)
    mem_vms = process.memory_info()[1] / float(2 ** 20)
    return mem, mem_vms


def version_cmd(argv=sys.argv[1:]):  # pragma: no cover
    """\
Print the version number of expose.

Usage:
  expose-version [options]

Options:
  -h --help                Show this screen.
"""
    docopt(version_cmd.__doc__, argv=argv)
    print(__version__)


@args_from_config
def upgrade(model_persister, from_version=None, to_version=None):
    kwargs = {'from_version': from_version}
    if to_version is not None:
        kwargs['to_version'] = to_version
    model_persister.upgrade(**kwargs)


def upgrade_cmd(argv=sys.argv[1:]):
    """\
Upgrade the database to the latest version.

Usage:
  expose-ugprade [options]

Options:
  --from=<v>               Upgrade from a specific version, overriding
                           the version stored in the database.

  --to=<v>                 Upgrade to a specific version instead of the
                           latest version.

  -h --help                Show this screen.
"""
    arguments = docopt(upgrade_cmd.__doc__, argv=argv)
    initialize_config(__mode__='fit')
    upgrade(from_version=arguments['--from'], to_version=arguments['--to'])


class PluggableDecorator:
    def __init__(self, decorator_config_name):
        self.decorator_config_name = decorator_config_name
        self.wrapped = None

    def __call__(self, func):
        self.func = func

        def wrapper(*args, **kwargs):
            """Defer loading the configuration until the function is
            called
            """

            if self.wrapped is None:
                func = self.func
                decorators = get_config().get(
                    self.decorator_config_name, [])
                self.decorators = [
                    resolve_dotted_name(dec) if isinstance(dec, str) else dec
                    for dec in decorators
                    ]
                orig_func = func
                for decorator in self.decorators:
                    func = decorator(func)
                if self.decorators:
                    self.wrapped = wraps(orig_func)(func)
                else:
                    self.wrapped = orig_func
            return self.wrapped(*args, **kwargs)

        return wraps(func)(wrapper)


def get_metadata(error_code=0, error_message=None, status='OK'):
    metadata = {
        'status': status,
        'error_code': error_code,
    }
    if error_message is not None:
        metadata['error_message'] = error_message
    metadata.update(get_config().get('service_metadata', {}))
    return metadata


def Partial(func, **kwargs):
    """Allows the use of partially applied functions in the
    configuration.
    """
    if isinstance(func, str):
        func = resolve_dotted_name(func)
    return partial(func, **kwargs)
