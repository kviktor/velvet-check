var API_URL = "https://localhost:5000/get_scores/";
var MAX_SPLIT_NUM = 6;

var urls = new Set();
var velvetLinks = $('.velvet.container a[href*="dex.hu"]');

velvetLinks.each(function(e) {
  var url = decodeURIComponent(gup("url", $(this).prop("href")));
  if(url.split("/").length > MAX_SPLIT_NUM) {
    urls.add(url);
  }
});

var key = hash(Array.from(urls).join()).toString();
chrome.storage.local.get(key, function(result) {
  if(key in result) {
    addScores(result[key]);
  } else {
    $.ajax({
      url: API_URL,
      method: "POST",
      data: JSON.stringify(Array.from(urls)),
      dataType: "json",
      contentType: "application/json; charset=utf-8",
      success: function(re) {
        chrome.storage.local.clear();

        if(!hasNullValue(re)) {
          var value = {}; value[key] = re;
          chrome.storage.local.set(value);
        }
        addScores(re);
      }
    });
  }
});

function addScores(scores) {
  velvetLinks.each(function() {
    var url = decodeURIComponent(gup("url", $(this).prop("href")));
    if(url.split("/").length > MAX_SPLIT_NUM && $(this).html().indexOf("<img") < 0) {
      if(scores[url] === null) {
        value = "-";
      } else {
        value = parseInt(scores[url] * 100) + "%";
      }
      $(this).append(" [" + value + "]");
    }
  });
}

function hasNullValue(obj) {
  for(var i in obj) {
    if(obj[i] === null) return true;
  }
  return false;
}


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


/*
 * http://stackoverflow.com/questions/7616461/generate-a-hash-from-string-in-javascript-jquery#comment14816892_7616484
 */
function hash(str) {
  var res = 0;
  var len = str.length;
  for (var i = 0; i < len; i++) {
    res = res * 31 + str.charCodeAt(i);
    res = res & res;
  }
  return res;
}
