# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

from setuptools import setup

PACKAGE_VERSION = '0.1'
deps = ['fxos-appgen>=0.2.7',
        'marionette_client>=0.7.1.1',
        'marionette_extension >= 0.1',
        'mozdevice >= 0.33',
        'mozlog >= 1.6',
        'moznetwork >= 0.24',
        'mozprocess >= 0.18',
        'wptserve >= 1.0.1',
        'wptrunner >= 0.2.6']

setup(name='fxos-certsuite',
      version=PACKAGE_VERSION,
      description='Certification suite for FirefoxOS',
      classifiers=[],
      keywords='mozilla',
      author='Mozilla Automation and Testing Team',
      author_email='tools@lists.mozilla.org',
      url='https://github.com/mozilla-b2g/fxos-certsuite',
      license='MPL',
      packages=['certsuite'],
      include_package_data=True,
      zip_safe=False,
      install_requires=deps,
      entry_points="""
      # -*- Entry points: -*-
      [console_scripts]
      runcertsuite = certsuite:harness_main
      cert = certsuite:certcli
      """)
