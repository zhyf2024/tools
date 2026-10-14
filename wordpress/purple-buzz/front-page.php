<?php
/**
 * Front page: hero, editor content, then the dynamic home sections.
 *
 * @package Purple_Buzz
 */

get_header();

get_template_part( 'template-parts/banner', 'carousel' );

// A static front page can hold editable blocks (CTA banner, pricing cards…).
if ( is_page() ) {
	while ( have_posts() ) {
		the_post();
		if ( trim( get_the_content() ) ) {
			?>
			<section class="container py-5">
				<div class="row">
					<div class="col-lg-10 mx-auto pb-4">
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
			<?php
		}
	}
}

get_template_part( 'template-parts/section', 'services' );
get_template_part( 'template-parts/section', 'cta' );
get_template_part( 'template-parts/section', 'recent-work' );

// When the front page shows the latest posts, list them under the sections.
if ( is_home() ) {
	?>
	<section class="container py-5">
		<div class="row text-center pb-5">
			<h2 class="col-md-6 m-auto h2 semi-bold-600 py-4"><?php esc_html_e( 'Latest Posts', 'purple-buzz' ); ?></h2>
		</div>
		<?php if ( have_posts() ) : ?>
			<div class="row">
				<?php
				while ( have_posts() ) {
					the_post();
					get_template_part( 'template-parts/content', 'card' );
				}
				?>
			</div>
			<?php purple_buzz_pagination(); ?>
		<?php else : ?>
			<?php get_template_part( 'template-parts/content', 'none' ); ?>
		<?php endif; ?>
	</section>
	<?php
}

get_footer();
