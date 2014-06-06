function closeMe()
{
  document.body.style.background = '#ff00ff';

  var xmlHttp = null;
  xmlHttp = new XMLHttpRequest();
  xmlHttp.open( "POST", RESULTS_URI, true );
  xmlHttp.setRequestHeader("Content-type", "application/x-www-form-urlencoded")
  xmlHttp.send("results={}");
  document.body.style.background = '#ff00ff';
}

window.addEventListener('load', function () {setTimeout(closeMe, 100);}, false);
