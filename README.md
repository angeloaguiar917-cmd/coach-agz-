<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Coach AGZ - Landing Page</title>
    <link rel="stylesheet" href="css/style.css">
</head>
<body>
    <!-- Your landing page content here -->
    
    <!-- PostHog Analytics -->
    <script>
        !function(t,e){var o,n,p,r;e.__SV||(window.posthog=e,e._i=[],e.init=function(i,s,a){function g(t,e){var o=e.split(".");2==o.length&&(t=t[o[0]]),t[o.length-1]]=a}(p=t.createElement("script")).type="text/javascript",p.async=!0,p.src="https://cdn.posthog.com/array.js",(r=t.getElementsByTagName("script")[0]).parentNode.insertBefore(p,r);var u=e;for(void 0===u._i&&(u._i=[]),u.i.push(arguments),u.__SV=1.2,o=0;o<e._i.length;++o)try{g(e._i[o][0],e._i[o][1])}catch(t){window.console&&console.log("PostHog identify failed",t)}}),e.capture=function(i,s,a,g){var u={event:i,properties:s,timestamp:a};null!==g&&(u.groups=g),e._e.push(u)},e.capturePageView=function(i,s){e.capture("$pageview",i,s)},e.reset=function(){document.cookie="ph_phc_"+e._i.join("")+"=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;"},e.config=function(t,i){e.__config=t,e.__configOptions=i},e.opt_out_capturing=function(){e.__disabled=!0},e.opt_in_capturing=function(){e.__disabled=!1},e.has_opted_out_capturing=function(){return e.__disabled===!0},e.has_opted_in_capturing=function(){return e.__disabled===!1},e.people=new Object,e.toString=function(){return"PostHog"},e._e=[],e._i=[[t,"posthog",!0]],e.init(t)}(document,window.posthog||[]);
        posthog.init('YOUR_POSTHOG_API_KEY', {api_host:'https://app.posthog.com'})
    </script>

    <script src="js/main.js"></script>
</body>
</html>
