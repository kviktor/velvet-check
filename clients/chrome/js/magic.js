alert("szia");

var links = new Set();

$('.velvet.container a[href*="dex.hu"]').each(function(e) {
    var url = decodeURIComponent(gup("url", $(this).prop("href")));
    if(url.split("/").length > 5) {
        links.add(url);
    }
});

console.log(links);


function gup( name, url ) {
    if (!url) url = location.href;
    name = name.replace(/[\[]/,"\\\[").replace(/[\]]/,"\\\]");
    var regexS = "[\\?&]"+name+"=([^&#]*)";
    var regex = new RegExp( regexS );
    var results = regex.exec( url );
    return results === null ? null : results[1];
}
