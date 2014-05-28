

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

      // attention
      // This should only be available to system apps, but we can see
      // if it shows up here.
      permissionsResults['attention'] = 'AttentionScreen' in window;

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

      // background-sensors
      // TODO: it appears this is only a planned feature at the moment

      // backgroundservice
      // TODO: it appears this is only a planned feature at the moment

      // bluetooth
      permissionsResults['bluetooth'] = 'mozBluetooth' in navigator;

      // browser
      // if mozbrowser is supported, we will see additional methods on the
      // iframe.
      var iframe = document.getElementById('test-mozbrowser');
      permissionsResults['browser'] = 'getScreenshot' in iframe;

      // camera
      permissionsResults['camera'] = 'mozCameras' in navigator;

      // cellbroadcast
      permissionsResults['cellbroadcast'] = 'mozCellBroadcast' in navigator;

      // contacts
      permissionsResults['contacts'] = navigator.mozContacts !== null;

      // deprecated-hwvideo
      // TODO: it appears this is only available to system apps and isn't
      //       testable here.

      // desktop-notification
      permissionsResults['desktop-notification'] = window.Notification !== null;

      // device-storage
      permissionsResults['device-storage:apps'] = navigator.getDeviceStorage('apps') !== null;
      permissionsResults['device-storage:crashes'] = navigator.getDeviceStorage('crashes') !== null;
      permissionsResults['device-storage:pictures'] = navigator.getDeviceStorage('pictures') !== null;
      permissionsResults['device-storage:videos'] = navigator.getDeviceStorage('videos') !== null;
      permissionsResults['device-storage:music'] = navigator.getDeviceStorage('music') !== null;
      permissionsResults['device-storage:sdcard'] = navigator.getDeviceStorage('sdcard') !== null;

      // downloads
      // TODO: is there a public api to test here or is this event driven?

      // embed-apps
      // TODO: not sure how to test whether the app loaded successfully 
      permissionsResults['embed-apps'] = false;

      // feature-detection
      // See: https://wiki.mozilla.org/WebAPI/Navigator.hasFeature
      permissionsResults['feature-detection'] = 'hasFeature' in navigator;

      // fmradio
      permissionsResults['fmradio'] = navigator.mozFMRadio !== null;

      // geolocation
      permissionsResults['geolocation'] = navigator.geolocation !== null;

      // idle
      permissionsResults['idle'] = 'addIdleObserver' in navigator;

      // input
      // See https://wiki.mozilla.org/WebAPI/KeboardIME
      permissionsResults['input'] = 'mozInputMethod' in navigator;

      // input-manage
      if ('mozInputMethod' in navigator) {
        permissionsResults['input-manage'] = 'mgmt' in navigator.mozInputMethod;
      } else {
        permissionsResults['input-manage'] = false;
      }

      // keyboard
      permissionsResults['keyboard'] = navigator.mozKeyboard !== null;

      // mobileconnection
      permissionsResults['mobileconnection'] = navigator.mozMobileConnection !== null;

      // mobilenetwork
      permissionsResults['mobilenetwork'] = 'mozMobileConnections' in navigator;
 
      // network-events
      // TODO: Not testable here - we need a suitable source of network events

      // nfc
      permissionsResults['nfc'] = 'mozNfc' in navigator;

      // nfc-manager
      if (permissionsResults['nfc']) {
        //TODO: this seems to allow additional nfc capabilities for the
        //      system app, but I don't have mozNfc, so I can't verify
        permissionsResults['nfc-manager'] = false;
      }

      // networkstats-manage
      // TODO: this appears to be used internally by the costcontrol app.
      //       not sure if there is anything to test here.

      // open-remote-window
      // If a remote window is opened, the returned handle will be null
      /* TODO: need to close the remote window automagically
      var win = window.open('about:blank', 'Remote Window', 'remote=true');
      permissionsResults['open-remote-window'] = win === null;
      */
      permissionsResults['open-remote-window'] = false; 

      // permissions
      permissionsResults['permissions'] = navigator.mozPermissions !== null;

      // phone number service
      // normalize and fuzzyMatch only exposed if permissions exist
      permissionsResults['phonenumberservice'] = 'normalize' in navigator.mozPhoneNumberService;
     
      // power
      permissionsResults['power'] = 'mozPower' in navigator;

      // push
      permissionsResults['push'] = navigator.push !== null;

      // settings
      permissionsResults['settings'] = navigator.mozSettings !== null;

      // sms
      permissionsResults['sms'] = 'mozMobileMessage' in navigator;

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

      // time
      permissionsResults['time'] = 'mozTime' in navigator;

      // tcp-socket
      permissionsResults['tcp-socket'] = navigator.mozTCPSocket !== null;

      // telephony
      permissionsResults['telephony'] = 'mozTelephony' in navigator;

      // voicemail
      permissionsResults['voicemail'] = 'mozVoicemail' in navigator;

      // wappush
      // Not testable here - these are received by using
      // mozSetMessageHandler to subscribe to 'wappush-received' messages.
      // Any app can subscribe but the messages are only delivered if
      // the corresponding permission is set. Without a way of injecting
      // 'wappush-received' messages we can't test this here.

      // webapps-manage
      permissionsResults['webapps-manage'] = navigator.mozApps.mgmt !== null;

      // wifi-manage
      permissionsResults['wifi-manager'] = navigator.mozWifiManager !== null;

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
