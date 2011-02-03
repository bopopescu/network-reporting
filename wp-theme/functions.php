<?php 
	add_theme_support( 'menus' );
	register_nav_menus(
		array(
		'footer_left_nav'=>__('Footer Left Menu'),
		'footer_right_nav'=>__('Footer Right Menu'),
		)
	);

	function is_child($pageID) { 
		global $post; 
		if( is_page() && ($post->post_parent==$pageID) ) {
	               return true;
		} else { 
	               return false; 
		}
	}
?>