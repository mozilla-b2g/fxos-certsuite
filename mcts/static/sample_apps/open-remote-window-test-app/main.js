function runTest()
{
  var win = window.open('remote-window.html', 'Remote Window', 'remote=true');

  var results = {}
  results['open-remote-window'] = win === null;

  var xmlHttp = null;
  xmlHttp = new XMLHttpRequest();
  xmlHttp.open( "POST", RESULTS_URI, true );
  xmlHttp.setRequestHeader("Content-type", "application/x-www-form-urlencoded")
  xmlHttp.send("results=" + JSON.stringify(results));
}

window.addEventListener('load', function () {setTimeout(runTest, 100);}, false);
