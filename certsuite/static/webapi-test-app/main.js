

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

function permissionsTests()
{
  // Create one promise for all of the synchronous APIs
  var syncAPIPromise = new Promise(
    function(resolve, reject) {
      var permissionsResults = {};

      // alarms
      permissionsResults['alarms'] = navigator.mozAlarms !== null;

      // For audio channel types, if we attempt to assign something for
      // which we do not have permissions, the channel type will remain
      // "normal".

      // audio-channel-alarm
      var audio = new Audio();
      audio.mozAudioChannelType = 'alarm';
      permissionsResults['audio-channel-alarm'] =  audio.mozAudioChannelType;

      // audio-channel-content
      var audio = new Audio();
      audio.mozAudioChannelType = 'content';
      permissionsResults['audio-channel-content'] = audio.mozAudioChannelType;

      // audio-channel-normal
      var audio = new Audio();
      audio.mozAudioChannelType = 'normal';
      permissionsResults['audio-channel-normal'] = audio.mozAudioChannelType;

      // audio-channel-notification
      var audio = new Audio();
      audio.mozAudioChannelType = 'notification';
      permissionsResults['audio-channel-notification'] = audio.mozAudioChannelType;

      // audio-channel-ringer
      var audio = new Audio();
      audio.mozAudioChannelType = 'ringer';
      permissionsResults['audio-channel-ringer'] = audio.mozAudioChannelType;

      // audio-channel-telephony
      var audio = new Audio();
      audio.mozAudioChannelType = 'telephony';
      permissionsResults['audio-channel-telephony'] = audio.mozAudioChannelType;

      // audio-channel-publicnotification 
      var audio = new Audio();
      audio.mozAudioChannelType = 'publicnotification';
      permissionsResults['audio-channel-publicnotification'] = audio.mozAudioChannelType;

      // browser
      // if mozbrowser is supported, we will see additional methods on the
      // iframe.
      var iframe = document.getElementById('test-mozbrowser');
      permissionsResults['browser'] = 'getScreenshot' in iframe;

      // contacts
      permissionsResults['contacts'] = navigator.mozContacts !== null;

      // desktop-notification 
      permissionsResults['desktop-notification'] = window.Notification !== null;

      // device-storage
      permissionsResults['device-storage:apps'] = navigator.getDeviceStorage('apps') !== null;
      permissionsResults['device-storage:crashes'] = navigator.getDeviceStorage('crashes') !== null;
      permissionsResults['device-storage:pictures'] = navigator.getDeviceStorage('pictures') !== null;
      permissionsResults['device-storage:videos'] = navigator.getDeviceStorage('videos') !== null;
      permissionsResults['device-storage:music'] = navigator.getDeviceStorage('music') !== null;
      permissionsResults['device-storage:sdcard'] = navigator.getDeviceStorage('sdcard') !== null;

      // fmradio 
      permissionsResults['fmradio'] = navigator.mozFMRadio !== null;

      // geolocation
      permissionsResults['geolocation'] = navigator.geolocation !== null;

      // keyboard
      permissionsResults['keyboard'] = navigator.mozKeyboard !== null;

      // mobilenetwork
      permissionsResults['mobilenetwork'] = navigator.mozMobileConnection !== null;

      // push 
      permissionsResults['push'] = navigator.push !== null;

      // storage 
      // TODO: not sure if this needs to be tested, allowed for all apps

      // systemXHR 
      var req = new XMLHttpRequest({'mozSystem': true});
      req.open('GET', 'http://192.168.1.100', false);
      var system_xhr = true; 
      try {
          req.send();
      } catch (err) {
          system_xhr = false; 
      }
      permissionsResults['systemXHR'] = system_xhr;

      // tcp-socket 
      permissionsResults['tcp-socket'] = navigator.mozTCPSocket !== null;

      resolve(permissionsResults);
  });

  // audio-capture
  var audioCapturePromise = new Promise(
    function(resolve, reject) {
      /* TODO: this is broken on some devices, disabling for now
      navigator.mozGetUserMedia({video: false, audio: true}, function(s) {
          resolve({'audio-capture': true});
      }, function(e) {
          resolve({'audio-capture': false});
      });
      */
      resolve({'audio-capture': false});
  });

  // video-capture
  var videoCapturePromise = new Promise(
    function(resolve, reject) {
      /* TODO: this is broken on some devices, disabling for now
      navigator.mozGetUserMedia({video: true, audio: false}, function(s) {
          resolve({'video-capture': true});
      }, function(e) {
          resolve({'video-capture': false});
      });
      */
      resolve({'video-capture': false});
  });

  return Promise.all([syncAPIPromise, audioCapturePromise, videoCapturePromise]);
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
  var winResults = getTheNames(window, {});

  var results = {};
  results.windowList = winResults;
  results.webIDLResults = webIDLResults;
  var permissionsPromise = permissionsTests();
  permissionsPromise.then(function(result) {
    results.permissionsResults = {};

    //combine results into one object
    result.forEach(function (o) {
      for (key in o) {
        results.permissionsResults[key] = o[key];
      }
    });

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
  });
}

window.addEventListener('load', function () {setTimeout(runTest, 100);}, false);
