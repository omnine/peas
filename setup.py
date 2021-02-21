#!/usr/bin/env python

from distutils.core import setup
import py2exe
setup(
    console=['peas/as_load_test.py'],
    options={
        'py2exe': {
            'packages': ['peas', 'peas.eas_client',
                'peas.pyActiveSync', 'peas.pyActiveSync.client', 'peas.pyActiveSync.objects', 'peas.pyActiveSync.utils']
        }
    }
)

"""
setup(name='PEAS',
      console=['peas/__main__.py'])


setup(name='PEAS',
      version='1.0',
      description='ActiveSync Library',
      author='Adam Rutherford',
      author_email='adam.rutherford@mwrinfosecurity.com',
      packages=['peas', 'peas.eas_client',
                'peas.pyActiveSync', 'peas.pyActiveSync.client', 'peas.pyActiveSync.objects', 'peas.pyActiveSync.utils'],
      scripts=['scripts/peas'],
     )
"""