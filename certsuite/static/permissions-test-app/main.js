/*
This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this file,
You can obtain one at http://mozilla.org/MPL/2.0/.
*/

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
      // TODO: Although this shows up in PermissionsTable.jsm,
      //       when installing we get PermissionsInstaller.jsm: 'downloads'
      //       is not a valid Webapps permission name.

      // embed apps
      // This is tested by running a separate app in an iframe which posts
      // its own results.

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
      // This needs to be tested in a separate app. Opening the remote
      // window could cause this app to stop which means the tests never
      // complete.

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
  var permissionsPromise = permissionsTests();
  permissionsPromise.then(function(result) {
    results = {};

    //combine results into one object
    result.forEach(function (o) {
      for (key in o) {
        results[key] = o[key];
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
