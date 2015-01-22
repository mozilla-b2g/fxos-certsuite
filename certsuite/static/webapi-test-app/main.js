/*
This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this file,
You can obtain one at http://mozilla.org/MPL/2.0/.
*/

setup({explicit_done:true, timeout_multiplier:10});

function log(msg)
{
    var xmlHttp = null;
    xmlHttp = new XMLHttpRequest({'mozSystem': true});
    xmlHttp.open( "POST", LOG_URI, true );
    xmlHttp.setRequestHeader("Content-type", "application/x-www-form-urlencoded")
    xmlHttp.send("log=" + msg);
}

function getTheNames(obj, visited)
{
  var orig_obj = obj;

  var result = {};
  visited[obj] = result;

  while (obj) {
    for (var name of Object.getOwnPropertyNames(obj)) {

      // work around crash - see Bug 1053246
      if (name === 'voice' || name === 'data') {
        continue;
      }

      try {
        var value = orig_obj[name];
        var value_visited = visited[value];
      } catch(err) {
        // We can hit a few exceptions here:
        // * some objects will throw "NS_ERROR_XPC_BAD_OP_ON_WN_PROTO: Illegal operation on WrappedNative prototype object" for the prototype property
        // * some objects will throw "Method not implemented" or similar when trying to access them by name
        result[name] = err;
        continue;
      }

      if (value === null) {
        result[name] = null;
      } else if (typeof value === "object") {
        if (value_visited === undefined) {
          result[name] = getTheNames(value, visited);
        } else {
          result[name] = true;
        }
      } else {
        result[name] = true;
      }
    }

    obj = Object.getPrototypeOf(obj);
  }

  return result;
}

function runTest()
{
  log('Starting webapi-test-app runTest()')

  // Run WebIDL test suite
  var webIDLResults = []

  add_test_started_callback(function (name) {
    log('WebIDL test started: ' + name);
  });

  add_completion_callback(function (tests) {
    tests.forEach(function (test) {
      var result;
      switch(test.status) {
        case test.PASS:
          result = 'PASS';
          break;
        case test.FAIL:
          result = 'FAIL';
          break;
        case test.TIMEOUT:
          result = 'TIMEOUT';
          break;
        case test.NOTRUN:
          result = 'NOTRUN';
          break;
      }
      webIDLResults.push({name:test.name, result:result, message:test.message});
    });
  });

  var idl_array = new IdlArray();

  TESTED_IDL.forEach(function (text) {
    idl = JSON.parse(text);
    idl_array.internal_add_idls([idl]);
  });
  TESTED_IDL = null;

  UNTESTED_IDL.forEach(function (text) {
    idl = JSON.parse(text);
    idl.untested = true;
    if ('members' in idl) {
      idl.members.forEach(function (member) {
        member.untested = true;
      });
    }
    idl_array.internal_add_idls([idl]);
  });
  UNTESTED_IDL = null;

  log('Running WebIDL tests');
  try {
    idl_array.test();
  } catch (e) {
    log('caught exception: ' + e.message);
  }
  done();

  //Recursively get property names on window object
  log('test started: "getTheNames" on window');
  var winResults = {}
  try {
    winResults = getTheNames(window, {});
  } catch (e) {
    log('caught exception: ' + e.message);
  }

  var results = {};
  results.windowList = winResults;
  results.webIDLResults = webIDLResults;

  var xmlHttp = null;
  xmlHttp = new XMLHttpRequest({'mozSystem': true});
  xmlHttp.open( "POST", RESULTS_URI, true );
  xmlHttp.setRequestHeader("Content-type", "application/x-www-form-urlencoded")
  xmlHttp.send("results=" + JSON.stringify(results));

  var status_el = document.getElementById('status');
  status_el.innerHTML = 'Done.';
}

window.addEventListener('load', function () {setTimeout(runTest, 100);}, false);
