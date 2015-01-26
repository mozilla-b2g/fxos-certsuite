Firefox OS Certification Testsuite for Stingray
===================================

Tests and tools to verify the functionality and characteristics of
Firefox OS on real devices.

Before running the tests, make sure you read the full documentation
at http://fxos-certsuite.readthedocs.org/ or in documentation.pdf
found in this directory.

Prerequest
--------------
1. git
2. python
3. pip (sudo easy_install pip)
4. virtualenv (sudo pip install virtualenv)
5. Install CertTest App using WebIDE

Instructions to run MCTS (suggest run in Ubuntu linux)
-----------------------------------------------------------------------
1. git clone https://github.com/Mozilla-TWQA/fxos-certsuite
2. cd fxos-certsuite
3. virtualenv stingray2.0
4. source stingray2.0/bin/activate
5. git checkout stingray
6. python setup.py install
7. runcertsuite --host 10.247.30.195

Note:Please change the IP address to IP of TV

Example
-----------
- List Tests
  ::

   	$ runcertsuite --host 10.247.30.195 --list-tests

- Run webapi Tests
  ::

   	$ runcertsuite  --host 10.247.30.195 webapi

- Run webapi:apps Test
  ::

   	$ runcertsuite --host 10.247.30.195  webapi:apps

- Run multiple Tests
  ::

   	$ runcertsuite --host 10.247.30.195  webapi:apps webapi:tcp_socket

