<?php get_header(); ?>

  <div id="titlebar">
    <div class="pageWidth">
      <h1><?php the_category(', ') ?></h1>
    </div>
  </div>

  <div id="content">
	<div class="pageWidth">
		<div class="content-main">
			
			<?php if (have_posts()) : ?>

				<?php while (have_posts()) : the_post(); ?>

				<section>
					<div class="post-date"><span class="post-month"><?php the_time('M') ?></span> <span class="post-day"><?php the_time('j') ?></span></div>
					<div class="post-title">
						<h2><?php the_title(); ?></h2>
					</div>
					<div class="entry">

						<?php the_content('Read the rest of this entry &raquo;'); ?>

						<?php wp_link_pages(array('before' => '<p><strong>Pages:</strong> ', 'after' => '</p>', 'next_or_number' => 'number')); ?>

					</div>
			
					<?php comments_template(); ?>
			
				</section>

				<?php endwhile; ?>


			<?php else : ?>

				<h2>Not Found</h2>
				<p>Sorry, but you are looking for something that isn't here.</p>

			<?php endif; ?>
		</div>
		<?php get_sidebar(); ?>
		
	</div>
  </div>
	
<?php get_footer(); ?>