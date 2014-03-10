# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

from setuptools import setup

PACKAGE_VERSION = '0.1'
deps = ['marionette_client==0.7.1']
        

setup(name='webapi_tests',
      version=PACKAGE_VERSION,
      description="Minimal tests for certification",
      classifiers=[],
      keywords='mozilla',
      author='Mozilla Automation and Testing Team',
      author_email='tools@lists.mozilla.org',
      url='https://github.com/mozilla-b2g/fxos-certsuite',
      license='MPL',
      packages=['webapi_tests'],
      include_package_data=True,
      zip_safe=False,
      install_requires=deps,
      entry_points="""
      """)
