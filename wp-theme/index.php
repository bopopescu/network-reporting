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
						<h2><a href="<?php the_permalink() ?>" rel="bookmark" title="Permanent Link to <?php the_title_attribute(); ?>"><?php the_title(); ?></a></h2>
					</div>
					<div class="entry">
						<?php the_content('Read the rest of this entry &raquo;'); ?>
					</div>
					
					<div>
						<a href="<?php the_permalink() ?>" title="<?php the_title(); ?>">Permalink</a>
					</div>
					
				</section>

				<?php endwhile; ?>

				<section class="navigation"> 
					<span class="previous-entries"><?php next_posts_link('Older Entries') ?></span>
					<span class="next-entries"><?php previous_posts_link('Newer Entries') ?></span> 
				</section>

			<?php else : ?>

				<h2>Not Found</h2>
				<p>No posts under this category.</p>

			<?php endif; ?>
		</div>
		<?php get_sidebar(); ?>
    </div>
  </div>

<?php get_footer(); ?>