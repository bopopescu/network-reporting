from string import Template

text_icon = Template(
"""<html>
  <head>
    $finishLoad
    <script> 
      if(typeof mopubFinishLoad == 'function') {
          window.onload = mopubFinishLoad;
      }
    </script>
    <script>
      function webviewDidClose(){}
      function webviewDidAppear(){}
    </script>
    <title></title>
  </head>
  <body style="top-margin:0;margin:0;width:320px;padding:0;background-color:#$color;font-size:12px;font-family:Arial,sans-serif;">
  <div id='highlight' style="position:relative;height:50px;background:-webkit-gradient(linear, left top, left bottom, from(rgba(255,255,255,0.35)),
    to(rgba(255,255,255,0.06))); -webkit-background-origin: padding-box; -webkit-background-clip: content-box;">
    <div style="margin:5px;width:40px;height:40px;float:left"><img id="thumb" src="$image_url" style="-webkit-border-radius:6px;-moz-border-radius:6px" width=40 height=40/></div>
    <div style="float:left;width:230">
      <div style="color:white;font-weight:bold;margin:0px 0 0 5px;padding-top:8;">$line1</div>
      <div style="color:white;margin-top:6px;margin:5px 0 0 5px;">$line2</div>
    </div>
    $action_icon_div
    $trackingPixel
  </div>
  </body>
</html>""")
