<?php
/*
Template Name: Features
*/
?>
<?php get_header(); ?>

  <div id="titlebar">
    <div class="pageWidth">
      <h1><?php the_title(); ?></h1>
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
			<h5>In-Depth</h5>  
			<ul>
			  <li><a href="/features">Summary</a></li>
			  <?php
			  global $id;
			  wp_list_pages("title_li=&child_of=172&show_date=modified&date_format=$date_format"); ?>
			</ul>	
		</aside>
		<?php get_sidebar(); ?>		
		
	</div>
  </div>
  <!--/content -->

<?php get_footer(); ?>