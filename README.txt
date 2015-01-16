Firefox OS Certification Testsuite for Stingray
===============================================

Tests and tools to verify the functionality and characteristics of
Firefox OS on real devices.

Before running the tests, make sure you read the full documentation
at http://fxos-certsuite.readthedocs.org/ or in documentation.pdf
found in this directory.

Prerequest:
1. git
2. python
3. pip (sudo easy_install pip)
4. virtualenv (sudo pip install virtualenv)

Instructions to run MCTS in FreeBSD 
1. git clone https://github.com/Mozilla-TWQA/fxos-certsuite
4. virtualenv stingray2.0
5. source stingray2.0/bin/activate
6. git checkout stingray
7. python setup.py install
8. runcertsuite webapi:bluetooth webapi:bluetooth webapi:device_storage webapi:idle webapi:moztime webapi:tcp_socket webapi:wifi webapi:apps cert:
