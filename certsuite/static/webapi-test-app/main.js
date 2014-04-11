

setup({explicit_done:true, timeout_multiplier:10});

function getTheNames(obj, visited)
{
  var orig_obj = obj;

  var result = {};
  visited[obj.toString()] = result;

  while (obj) {
    for (var name of Object.getOwnPropertyNames(obj)) {
      try {
        var value = orig_obj[name];
        var value_name = value.toString();
        var type = typeof(value);
      } catch(err) {
        result[name] = err;
        continue;
      }

      if (value === null) {
        result[name] = null;
      } else if (type === "object") {
        if (!visited[value_name]) {
          getTheNames(value, visited);
        }
        result[name] = value_name;
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

  var navResults = {};
  getTheNames(navigator, navResults);

  var winResults = {};
  getTheNames(window, winResults);

  var results = {};
  results.navList = navResults;
  results.windowList = winResults;
  results.webIDLResults = webIDLResults;

  var xmlHttp = null;
  xmlHttp = new XMLHttpRequest();
  try {
      // if we have a RESULTS_URI, use that, otherwise default to origin
      console.log('>>>>>>>>>>', RESULTS_URI);
      xmlHttp.open( "POST", RESULTS_URI, true );
  } catch (e) {
      console.log('>>>>>>>>>> NO RESULTS_URI');
      xmlHttp.open( "POST", location.origin + "/webapi_results", true );
  }
  xmlHttp.setRequestHeader("Content-type", "application/x-www-form-urlencoded")
  xmlHttp.send("results=" + JSON.stringify(results));

  var status_el = document.getElementById('status');
  status_el.innerHTML = 'Done.';
}

window.addEventListener('load', function () {setTimeout(runTest, 100);}, false);
