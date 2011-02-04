<?php
/*
Template Name: Features
*/
?>
<?php get_header(); ?>

  <div id="titlebar">
    <div class="pageWidth">
      <h1><?php if (is_child(172)) { echo '<a href="/features">Features</a> &raquo;'; }?> <?php the_title(); ?></h1>
    </div>
  </div>

  <div id="content">
	<div class="pageWidth">
		<div class="content-main">

			
			<?php if (have_posts()) : ?>

				<?php while (have_posts()) : the_post(); ?>
				<section>
					<?php the_content('Read the rest of this entry &raquo;'); ?>
				</section>
				<?php endwhile; ?>

			<?php else : ?>

				<h2>Not Found</h2>
				<p>Sorry, but you are looking for something that isn't here.</p>

			<?php endif; ?>			
		</div>
		<aside>
			<h5>MoPub In-Depth</h5>  
			<ul>
			  <?php
			  global $id;
			  wp_list_pages("title_li=&child_of=172&orderby=menu_order&order=desc&show_date=modified&date_format=$date_format"); ?>
			</ul>	
		</aside>
		<?php get_sidebar(); ?>		
		
	</div>
  </div>
  <!--/content -->

<?php get_footer(); ?>