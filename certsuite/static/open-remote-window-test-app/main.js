function runTest()
{
  window.close();
  var win = window.open('remote-window.html', 'Remote Window', 'remote=true');
}

window.addEventListener('load', function () {setTimeout(runTest, 100);}, false);
