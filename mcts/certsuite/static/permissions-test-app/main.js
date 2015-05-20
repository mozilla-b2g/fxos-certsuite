/*
This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this file,
You can obtain one at http://mozilla.org/MPL/2.0/.
*/

function log(msg)
{
    var xmlHttp = null;
    xmlHttp = new XMLHttpRequest();
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

      // device-storage
      permissionsResults['device-storage:apps'] = navigator.getDeviceStorage('apps') !== null;
      permissionsResults['device-storage:crashes'] = navigator.getDeviceStorage('crashes') !== null;
      permissionsResults['device-storage:pictures'] = navigator.getDeviceStorage('pictures') !== null;
      permissionsResults['device-storage:videos'] = navigator.getDeviceStorage('videos') !== null;
      permissionsResults['device-storage:music'] = navigator.getDeviceStorage('music') !== null;
      permissionsResults['device-storage:sdcard'] = navigator.getDeviceStorage('sdcard') !== null;

      // speaker-control
      permissionsResults['speaker-control'] = true;
      try {
        var sm = new MozSpeakerManager();
      } catch (err) {
        permissionsResults['speaker-control'] = false;
      }

      // storage
      // TODO: This permission removes limitations on how much device storage
      //       can be used by the application cache and indexeddb. It is
      //       difficult to test in a way that does not OOM my device.

      // systemXHR
      var req = new XMLHttpRequest({'mozSystem': true});
      req.open('GET', 'http://www.mozilla.org', false);
      var system_xhr = true;
      try {
          req.send();
      } catch (err) {
          system_xhr = false;
      }
      permissionsResults['systemXHR'] = system_xhr;

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

  // network-events
  // TODO: The network events are associated with using the data network
  //       but the test framework assumes the use of wifi, so this test
  //       will always return false for now.
  var networkEventsPromise = new Promise(
    function(resolve, reject) {

      addEventListener('moznetworkdownload', function (evt) {
        resolve({'network-events': true});
      });

      var iframe = document.createElement('iframe');
      document.body.appendChild(iframe);
      iframe.src = 'http://example.org';
      iframe.onload = function () {
        // Allow some time for the moznetworkdownload to fire
        setTimeout(function () {
          resolve({'network-events': false});
        }, 100);
      };
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

  // wappush
  // TODO: This test is expected to fail as we are not currently injecting
  //       any wappush events into the system for this to receive.
  var wappushPromise = new Promise(
    function(resolve, reject) {

      navigator.mozSetMessageHandler('wappush-received', function (msg) {
        resolve({'wappush': true});
      });

      // Eventually timeout if we never receive an wappush
      setTimeout(function () {
        resolve({'wappush': false});
      }, 1000);
  });

  return Promise.all([syncAPIPromise, audioCapturePromise, networkEventsPromise, videoCapturePromise, wappushPromise]);
}

function runTest()
{
  log('Starting permissions-test-app runTest()');

  var results = {}
  try {
    results['window'] = getTheNames(window, {});
  } catch (e) {
    log('caught exception: ' + e.message);
  }

  var permissionsPromise = permissionsTests();
  permissionsPromise.then(function(result) {

    //combine results into one object
    result.forEach(function (o) {
      for (key in o) {
        // only report true values for permissions
        if (o[key]) {
          results[key] = o[key];
        }
      }
    });

    var xmlHttp = null;
    xmlHttp = new XMLHttpRequest();
    xmlHttp.open( "POST", RESULTS_URI, true );
    xmlHttp.setRequestHeader("Content-type", "application/x-www-form-urlencoded")
    xmlHttp.send("results=" + JSON.stringify(results));

    var status_el = document.getElementById('status');
    status_el.innerHTML = 'Done.';
  });
}

window.addEventListener('load', function () {setTimeout(runTest, 100);}, false);
