This suite is intended to compare between golden samples and DUT(Device Under Test).

For certsuite owner, you need to do the following steps to generate the golden sample.

0. make sure /FirefoxOS/fxos-certsuite/mcts/static/sample_apps/ is correct
   Also, restart your phone and make sure you connect to Wifi of the same internet zone with your PC

In /fxos-certsuite/mcts/certsuite, do the following steps.
1. > python cert.py --include webapi --generate-reference
   copy 3 json files to /fxos-certsuite/mcts/static/expected_results/expected_webapi_results
2. > python cert.py --include omni-analyzer --generate-reference
   copy 3 json files to /fxos-certsuite/mcts/static/expected_results/expected_omni_results
3. > python cert.py --include permissions --generate-reference
   copy 3 json files to /fxos-certsuite/mcts/static/expected_results/expected_permissions_results

Finally, it's the last step for generating golden sample.
4. remove generated files, reinstall mcts, restart the phone, and rerun mcts

It should all pass now.



For normal runner, you may run this in 2 different ways.

a. > runcertsuite cert
   this should run all the cert suite tests
   > runcertsuite cert:webapi
   this should only run webapi cert tests

b. > python cert.py
   this should run all the cert suite tests
   > python cert.py --include webapi
   this should run all the cert suite tests
