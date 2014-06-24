addEventListener("DOMContentLoaded", function() {
  var r = document.getElementById("results");
  for (var i = 0; i < results.length; i++) {
    var tr = document.createElement("tr");
    var link = results[i].shortname + "/" + results[i].shortname + "_structured.html";
    var status = results[i].passed ? 'PASSED' : 'FAILED';
    tr.innerHTML = '<td><a href="' + link + '">' + results[i].name + '</td><td class="' + status + '">' + status + '</td>';
    r.appendChild(tr);
  }
}, true);
