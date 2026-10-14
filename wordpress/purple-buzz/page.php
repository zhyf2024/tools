<?php
/**
 * Default page template.
 *
 * @package Purple_Buzz
 */

get_header();

while ( have_posts() ) {
	the_post();

	purple_buzz_page_banner( get_post_meta( get_the_ID(), 'pb_subtitle', true ) );
	?>

	<main id="primary" class="site-main">
		<section class="container py-5">
			<div class="row">
				<div class="col-lg-10 mx-auto">
					<?php
					the_content();
					wp_link_pages(
						array(
							'before' => '<div class="page-links pb-3">' . esc_html__( 'Pages:', 'purple-buzz' ),
							'after'  => '</div>',
						)
					);
					?>
				</div>
			</div>
		</section>

		<?php if ( comments_open() || get_comments_number() ) : ?>
			<section class="container pb-5">
				<div class="row">
					<div class="col-lg-10 mx-auto">
						<?php comments_template(); ?>
					</div>
				</div>
			</section>
		<?php endif; ?>
	</main>

	<?php
}

get_footer();
