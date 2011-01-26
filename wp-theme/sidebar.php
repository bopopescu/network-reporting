  <?php if (is_page('features') || is_child('features')) { echo get_sidebar('features'); } ?>

  <aside>
		<h5>Category</h5>
		<ul class="ul-cat">
			<?php wp_list_categories('show_count=1&title_li='); ?>
		</ul>
  </aside>
  <aside>
    	
		<h5>Archives</h5>
		<ul class="ul-archives">
			<?php wp_get_archives('type=monthly'); ?>
		</ul>
  </aside>