<?php
/**
 * Single work item: banner, content, media gallery, related work, comments.
 *
 * @package Purple_Buzz
 */

get_header();

while ( have_posts() ) {
	the_post();

	$pb_subtitle = get_post_meta( get_the_ID(), 'pb_subtitle', true );
	if ( ! $pb_subtitle ) {
		$pb_subtitle = get_the_excerpt();
	}

	purple_buzz_page_banner( wp_trim_words( wp_strip_all_tags( $pb_subtitle ), 20 ) );
	?>

	<main id="primary" class="site-main">
		<section class="container py-5">

			<div class="row pt-5">
				<div class="worksingle-content col-lg-8 m-auto text-left justify-content-center">
					<div class="entry-content light-300 text-muted py-3">
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
			</div>

			<?php get_template_part( 'template-parts/work', 'gallery' ); ?>

		</section>

		<?php if ( comments_open() || get_comments_number() ) : ?>
			<section class="container pb-5">
				<div class="row">
					<div class="col-lg-8 m-auto">
						<?php comments_template(); ?>
					</div>
				</div>
			</section>
		<?php endif; ?>

		<?php
		$pb_related = new WP_Query(
			array(
				'post_type'      => 'work',
				'posts_per_page' => 3,
				'post__not_in'   => array( get_the_ID() ),
				'orderby'        => 'rand',
				'no_found_rows'  => true,
			)
		);

		if ( $pb_related->have_posts() ) :
			?>
			<article class="container-fluid bg-light">
				<div class="container">
					<div class="worksingle-related-header row">
						<h2 class="h2 py-5"><?php esc_html_e( 'Related Post', 'purple-buzz' ); ?></h2>
						<div class="col-md-12 text-left justify-content-center">
							<div class="row gx-5">
								<?php
								while ( $pb_related->have_posts() ) {
									$pb_related->the_post();
									?>
									<div class="col-sm-6 col-lg-4 mb-5">
										<a href="<?php the_permalink(); ?>" class="related-content card text-decoration-none overflow-hidden h-100">
											<img class="related-img card-img-top" src="<?php echo esc_url( purple_buzz_thumbnail_url() ); ?>" alt="<?php the_title_attribute(); ?>" width="800" height="600" loading="lazy">
											<div class="related-body card-body p-4">
												<h3 class="card-title h6 m-0 semi-bold-600 text-dark"><?php the_title(); ?></h3>
												<p class="card-text pt-2 mb-1 light-300 text-dark">
													<?php echo wp_kses_post( get_the_excerpt() ); ?>
												</p>
												<div class="d-flex justify-content-between">
													<span class="text-primary light-300"><?php esc_html_e( 'Read more', 'purple-buzz' ); ?></span>
												</div>
											</div>
										</a>
									</div>
									<?php
								}
								wp_reset_postdata();
								?>
							</div>
						</div>
					</div>
				</div>
			</article>
			<?php
		endif;
		?>

	</main>

	<?php
}

get_footer();
