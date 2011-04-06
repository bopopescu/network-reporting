from string import Template

html = Template("""<html><head><title>$title</title>
                        $finishLoad
                        <script type="text/javascript">
                          function webviewDidClose(){}
                          function webviewDidAppear(){}
                          window.addEventListener("load", function() {
                            var links = document.getElementsByTagName('a');
                            for(var i=0; i < links.length; i++) {
                              links[i].setAttribute('target','_blank');
                            }
                          }, false);
                        </script>$network_style</head>
                        <body class="network_center" style="margin:0;padding:0;">${html_data}$trackingPixel</body></html>""")

