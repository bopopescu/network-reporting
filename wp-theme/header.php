<!doctype html>  

<!--[if lt IE 7 ]> <html lang="en" class="no-js ie6"> <![endif]-->
<!--[if IE 7 ]>    <html lang="en" class="no-js ie7"> <![endif]-->
<!--[if IE 8 ]>    <html lang="en" class="no-js ie8"> <![endif]-->
<!--[if IE 9 ]>    <html lang="en" class="no-js ie9"> <![endif]-->
<!--[if (gt IE 9)|!(IE)]><!--> <html lang="en" class="no-js"> <!--<![endif]-->
<head>
  <meta charset="utf-8">
  <base href="<?php bloginfo('template_url'); ?>/">

  <title>MoPub</title>
  <meta name="description" content="">
  <meta name="author" content="">

  <link rel="shortcut icon" href="<?php bloginfo('template_url'); ?>/favicon.ico">
  <link rel="apple-touch-icon" href="<?php bloginfo('template_url'); ?>/apple-touch-icon.png">

  <!-- CSS -->
  <link rel="stylesheet" href="<?php bloginfo('template_url'); ?>/js/mylibs/jquery-ui-1.8.7.custom/css/mopub/jquery-ui-1.8.7.custom.css" />  
  <link rel="stylesheet" href="<?php bloginfo('template_url'); ?>/css/style.css">
  
  <!-- modernizr -->
  <script src="<?php bloginfo('template_url'); ?>/js/libs/modernizr-1.6.min.js"></script>
  
  <!-- TypeKit -->
  <script type="text/javascript" src="http://use.typekit.com/qhz7iwb.js"></script>
  <script type="text/javascript">try{Typekit.load();}catch(e){}</script>
  
  <!-- jQuery and jQuery UI -->
  <script src="https://ajax.googleapis.com/ajax/libs/jquery/1.4.4/jquery.min.js"></script>
  <script>!window.jQuery && document.write(unescape('%3Cscript src="js/mylibs/jquery-1.4.4.min.js"%3E%3C/script%3E'))</script>
  <script src="<?php bloginfo('template_url'); ?>/js/mylibs/jquery-ui-1.8.7.custom/js/jquery-ui-1.8.7.custom.min.js"></script>
  <script src="<?php bloginfo('template_url'); ?>/js/mylibs/jquery.placeholder.js"></script>
  <script src="<?php bloginfo('template_url'); ?>/js/mylibs/jquery.qtip-1.0.0-rc3.min.js"></script>
  <script src="<?php bloginfo('template_url'); ?>/js/mylibs/jquery.text-overflow.min.js"></script>

  <!-- Highcharts -->
  <script src="<?php bloginfo('template_url'); ?>/js/mylibs/highcharts/highcharts.js"></script>
  
  <!-- MoPub -->
  <script src="<?php bloginfo('template_url'); ?>/js/plugins.js"></script>
  <script src="<?php bloginfo('template_url'); ?>/js/mopub.js"></script>
  <script src="<?php bloginfo('template_url'); ?>/js/mopub-public.js"></script>
  
  <!--[if lt IE 7 ]>
    <script src="<?php bloginfo('template_url'); ?>/js/libs/dd_belatedpng.js"></script>
    <script> DD_belatedPNG.fix('img, .png_bg'); </script>
  <![endif]-->
</head>

<?php if (is_front_page()) { echo '<body class="mopub-public mopub-home" id="mopub-home-alt1">'; } 
	  else { echo '<body class="mopub-public">'; } ?>
		
  <div id="container">
    <a class="visuallyhidden" href="#main">Skip navigation</a>
    <div id="jsnotice">
      JavaScript is currently disabled. This site requires JavaScript to function correctly.
      Please <a href="http://enable-javascript.com/"> enable JavaScript in your browser</a>!
    </div>
    
    <header>
      <div class="pageWidth">
        <div id="logo"><a class="ir" href="/">MoPub</a></div>
        
        <nav id="nav1">
          <ul>
            <li <?php if (is_front_page()) { echo 'class="active"';}?>><a href="/">Home</a></li>
            <li <?php if (is_page_template('features.php')) { echo 'class="active"';}?>><a href="/features">Features</a></li>
            <li <?php if (is_page_template('archives.php') || is_category() || is_month() ) { echo 'class="active"';}?>><a href="/mopubblog">Blog</a></li>
            <li><a href="http://ads.mopub.com/welcome">Login</a></li>
          </ul>
        </nav>
        
        <nav id="nav2">
          <div id="header-icons">
            <!--a class="ir" id="header-icons-rss" href="rss.html">RSS</a-->
            <a class="ir" id="header-icons-twitter" href="http://twitter.com/mopub">Twitter</a>
          </div>
        </nav>
      </div>
    </header>

	<div id="main">
