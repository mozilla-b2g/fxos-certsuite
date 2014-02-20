# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

from setuptools import setup

PACKAGE_VERSION = '1.3.0.1'
deps = ['mozdevice >= 0.33',
        'moznetwork >= 0.24',
        "wptserve >= 1.0.1"]

setup(name='fxos-certsuite',
      version=PACKAGE_VERSION,
      description="Certification suite for FirefoxOS",
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
      cert = certsuite:certcli
      """)
