

setup({explicit_done:true, timeout_multiplier:10});

function getTheNames(obj, visited)
{
  var orig_obj = obj;

  var result = {};
  visited[obj] = result;

  while (obj) {
    for (var name of Object.getOwnPropertyNames(obj)) {
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

  // Run WebIDL test suite
  var webIDLResults = []
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

  idl_array.test();
  done();

  //Recursively get property names on window object
  var winResults = {};
  getTheNames(window, winResults);

  var results = {};
  results.windowList = winResults;
  results.webIDLResults = webIDLResults;

  var xmlHttp = null;
  xmlHttp = new XMLHttpRequest();
  try {
      // if we have a RESULTS_URI, use that, otherwise default to origin
      xmlHttp.open( "POST", RESULTS_URI, true );
  } catch (e) {
      xmlHttp.open( "POST", location.origin + "/webapi_results", true );
  }
  xmlHttp.setRequestHeader("Content-type", "application/x-www-form-urlencoded")
  xmlHttp.send("results=" + JSON.stringify(results));

  var status_el = document.getElementById('status');
  status_el.innerHTML = 'Done.';
}

window.addEventListener('load', function () {setTimeout(runTest, 100);}, false);
