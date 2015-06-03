# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

from setuptools import setup, find_packages

PACKAGE_VERSION = '0.1'

# dependencies
with open('requirements.txt') as f:
    deps = f.read().splitlines()

setup(name='fxos-certsuite',
      version=PACKAGE_VERSION,
      description='Certification suite for Firefox OS',
      classifiers=[],
      keywords='mozilla',
      author='Mozilla Automation and Testing Team',
      author_email='tools@lists.mozilla.org',
      url='https://github.com/mozilla-b2g/fxos-certsuite',
      license='MPL',
      packages=find_packages(),
      include_package_data=True,
      zip_safe=False,
      install_requires=deps,
      entry_points={"console_scripts": ["runcertsuite = mcts:harness_main",
                                        "securityrunner = mcts.securitysuite:securitycli",
                                        "cert = mcts.certsuite:certcli",
                                        "webapirunner = mcts.webapi_tests.runner:main"]})
