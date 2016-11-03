var API_URL = "http://localhost:5000/get_scores/";

var urls = new Set();
var velvetLinks = $('.velvet.container a[href*="dex.hu"]');

velvetLinks.each(function(e) {
  var url = decodeURIComponent(gup("url", $(this).prop("href")));
  if(url.split("/").length > 5) {
      urls.add(url);
  }
});

$.ajax({
  url: API_URL,
  method: "POST",
  data: JSON.stringify(Array.from(urls)),
  dataType: "json",
  contentType: "application/json; charset=utf-8",
  success: function(re) {
    velvetLinks.each(function(e) {
        var url = decodeURIComponent(gup("url", $(this).prop("href")));
        if(url.split("/").length > 5 && $(this).html().indexOf("<img") < 0) {
          if(re[url] === null) {
            value = "-";
          } else {
            value = parseInt(re[url] * 100) + "%";
          }
          $(this).append(" [" + value + "]");
        }
    });
  }
});


/*
 * http://stackoverflow.com/questions/979975/how-to-get-the-value-from-the-get-parameters
 * ¯\_(ツ)_/¯
 */
function gup( name, url ) {
    if (!url) url = location.href;
    name = name.replace(/[\[]/,"\\\[").replace(/[\]]/,"\\\]");
    var regexS = "[\\?&]"+name+"=([^&#]*)";
    var regex = new RegExp( regexS );
    var results = regex.exec( url );
    return results === null ? null : results[1];
}
