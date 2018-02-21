import pkg_resources

try:
    __version__ = pkg_resources.get_distribution("expose").version
except:
    __version__ = 'n/a'
