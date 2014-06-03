function runTest()
{
  results = {'embed-apps': true}

  // If 'mozapp' succeeds, we will be running as an app and have
  // permissions to change the audio channel here because we asked
  // for them in our manifest.
  var audio = new Audio();
  audio.mozAudioChannelType = 'content';
  if (audio.mozAudioChannelType == 'content') {
    document.body.style.background = '#00ffff';
    results['embed-apps'] = true;
  } else {
    document.body.style.background = '#ff00ff';
    results['embed-apps'] = false;
  }

  var xmlHttp = null;
  xmlHttp = new XMLHttpRequest();
  xmlHttp.open("POST", RESULTS_URI, true);
  xmlHttp.setRequestHeader("Content-type", "application/x-www-form-urlencoded")
  xmlHttp.send("results=" + JSON.stringify(results));
}

window.addEventListener('load', function () {setTimeout(runTest, 10);}, false);
