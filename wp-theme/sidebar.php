
  <aside>
		<h5>Blog Categories</h5>
		<ul class="ul-cat">
			<?php wp_list_categories('show_count=1&title_li='); ?>
		</ul>
  </aside>
  <aside>
    	
		<h5>Blog Archives</h5>
		<ul class="ul-archives">
			<?php wp_get_archives('type=monthly'); ?>
		</ul>
  </aside>