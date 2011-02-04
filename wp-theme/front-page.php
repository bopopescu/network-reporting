<?php get_header(); ?>

      <div id="titlebar">
        <div class="pageWidth">

			<?php
			global $post;
			$myposts = get_posts( array( 'numberposts' => 1, 'offset'=> 0, 'post_parent' => 189, 'post_type' => 'page', 'orderby' => 'menu_order', 'order' => 'ASC' ) );
			foreach( $myposts as $post ) :	setup_postdata($post); ?>
          		<div id="home-intro">
					<h1 id="home-headline"><?php the_title(); ?></h1>
					<?php the_content(); ?>

		            <div id="home-cta">
		              <span class="buttonWrap"><a class="button button-big" href="http://www.mopub.com/start/">Sign up now</a></span>
		              <span class="sep">&middot;</span>
		              <a href="/features">Learn more</a>
		            </div>
				</div>
				
				<?php				
				$args = array( 'post_type' => 'attachment', 'numberposts' => -1, 'post_status' => null, 'post_parent' => $post->ID ); 
				$attachments = get_posts($args);
				if ($attachments) {
					foreach ( $attachments as $attachment ) { ?>
						
						<div id="home-graphic">
						  <img src="<?php echo wp_get_attachment_url($attachment->ID); ?>" alt="" width="535" height="300" />
						</div>
						
				<?php
					}
				}
			endforeach; ?>

        </div>
        
        <!--div id="home-banner">
          <span class="inner1"><span class="inner2"><span class="inner3">
            <strong>NNN</strong> Impressions Served! Yeah!
          </span></span></span>
        </div-->

      </div>
      <div id="content">
        <div class="pageWidth">
          <section class="home-features">
			<?php
			global $post;
			$myposts = get_posts( array( 'numberposts' => 3, 'offset'=> 1, 'post_parent' => 189, 'post_type' => 'page', 'orderby' => 'menu_order', 'order' => 'ASC' ) );
			foreach( $myposts as $post ) :	
				setup_postdata($post); 
				$attachments = get_posts(array( 'post_type' => 'attachment', 'numberposts' => -1, 'post_status' => null, 'post_parent' => $post->ID ));?>
			            <div class="home-feature" id="home-feature-<?php echo ($post->menu_order - 1) % 3 + 1?>">
						
						  <?php if ($attachments) {
								foreach ( $attachments as $attachment ) { ?>
			              			<img class="home-feature-graphic" src="<?php echo wp_get_attachment_url($attachment->ID); ?>" alt="" width=290 height=150 />
						  <?php } 
							} ?>

			              <h3><?php the_title(); ?></h3>
			              <p>
			                <?php the_content(); ?>
			              </p>
				          <section>
				            <a href="<?php echo get_post_meta($post->ID, 'more', true)?>">Learn more &raquo;</a>
				          </section>

			            </div>
				<?php				
			endforeach;	?>				
				
          </section>
		  <div class="hr"></div>
		
		  <h2>Company News</h2>
          <section class="home-features">
			<?php
			global $post;
			$myposts = get_posts( array( 'numberposts' => 3, 'offset'=> 4, 'post_parent' => 189, 'post_type' => 'page', 'orderby' => 'menu_order', 'order' => 'ASC' ) );
			foreach( $myposts as $post ) :	
				setup_postdata($post); 
				$attachments = get_posts(array( 'post_type' => 'attachment', 'numberposts' => -1, 'post_status' => null, 'post_parent' => $post->ID ));?>
			            <div class="home-feature" id="home-feature-<?php echo ($post->menu_order - 1) % 3 + 1?>">
						
						  <?php if ($attachments) {
								foreach ( $attachments as $attachment ) { ?>
			              			<img class="home-feature-graphic" src="<?php echo wp_get_attachment_url($attachment->ID); ?>" alt="" width=290 height=150 />
						  <?php } 
							} ?>

			              <h3><?php the_title(); ?></h3>
			              <p>
			                <?php the_content(); ?>
			              </p>
				          <section>
				            <a href="<?php echo get_post_meta($post->ID, 'more', true)?>">Learn more &raquo;</a>
				          </section>

			            </div>
				<?php				
			endforeach;	?>								
          </section>

          <div class="clear"></div>
          <section id="mopub-public-cta">
            <span class="buttonWrap"><a class="button button-big" href="http://www.mopub.com/start/">Sign up now</a></span>
            <span class="sep">&middot;</span>
            <a href="/features">Learn more</a>
          </section>
		
        </div>
      </div>
    
    
<?php get_footer(); ?>