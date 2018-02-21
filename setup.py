import os
from setuptools import setup, find_packages

version = open('VERSION').read().rstrip()

# Conda environment provided with the modules
install_requires = [
    'docopt',
    'flask',
    'joblib',
    'numpy',
    'pandas',
    'psutil',
    'scikit-learn',
    'sqlalchemy',
    'ujson',
    ]

tests_require = [
    'pytest',
    'pytest-cov',
    ]

here = os.path.abspath(os.path.dirname(__file__))
try:
    README = open(os.path.join(here, 'README.md')).read()
except IOError:
    README = CHANGES = ''


setup(name = 'model_expose',
      version = version,
      description = 'Framework for predictive analytics models',
      long_description = README,
      url = 'https://github.com/trallard/Expose_test',
      author='Tania Allard',
      author_email='tania.sanchezmonroy@gmail.com',
      license = 'MIT',
      classifiers=[
          'Development Status :: 4 - Beta',
          'Intended Audience :: Developers',
          'License :: OSI Approved :: MIT License',
          'Programming Language :: Python :: 3'
      ],
      packages = find_packages(),
      include_package_data = True,
      zip_safe = False,
      install_requires = install_requires,
      extras_require = {
          'testing': tests_require,
          'julia': ['julia'],
          'R': ['rpy2'],
          },
      entry_points={
          'console_scripts': [
              'expose-admin = expose.fit:admin_cmd',
              'expose-devserver = expose.server:devserver_cmd',
              'expose-fit = expose.fit:fit_cmd',
              'expose-grid-search = expose.fit:grid_search_cmd',
              'expose-list = expose.eval:list_cmd',
              'expose-stream = expose.server:stream_cmd',
              'expose-test = expose.eval:test_cmd',
              'expose-upgrade = expose.util:upgrade_cmd',
              'expose-version = expose.util:version_cmd',
              ],
          'pytest11': [
              'expose = expose.tests',
              ],
          },
      scripts=['bin/expose-dockerize'],
      )
