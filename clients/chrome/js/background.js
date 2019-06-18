var API_URL = "http://localhost:5000/get_scores/";


chrome.runtime.onMessage.addListener(
  function(request, sender, sendResponse) {
    if (request.contentScriptQuery == "get_scores") {
      $.ajax({
        url: API_URL,
        method: "POST",
        data: JSON.stringify(request.urls),
        dataType: "json",
        contentType: "application/json; charset=utf-8",
        success: function(re) {
          sendResponse({'scores': re});
        }
      });
      return true;
    }
  });
