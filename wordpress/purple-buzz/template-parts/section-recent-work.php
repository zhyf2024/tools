<?php
/**
 * Recent work section on the home page.
 *
 * @package Purple_Buzz
 */

$pb_work = new WP_Query(
	array(
		'post_type'      => 'work',
		'posts_per_page' => 6,
		'no_found_rows'  => true,
	)
);

if ( ! $pb_work->have_posts() ) {
	return;
}
?>
<!-- Start Recent Work -->
<section class="py-5 mb-5">
	<div class="container">
		<div class="recent-work-header row text-center pb-5">
			<h2 class="col-md-6 m-auto h2 semi-bold-600 py-5"><?php esc_html_e( 'Recent Works', 'purple-buzz' ); ?></h2>
		</div>
		<div class="row gy-5 g-lg-5 mb-4">

			<?php
			while ( $pb_work->have_posts() ) {
				$pb_work->the_post();
				?>
				<div class="col-md-4 mb-3">
					<a href="<?php the_permalink(); ?>" class="recent-work card border-0 shadow-lg overflow-hidden">
						<img class="recent-work-img card-img" src="<?php echo esc_url( purple_buzz_thumbnail_url( get_the_ID(), 'large' ) ); ?>" alt="<?php the_title_attribute(); ?>" width="800" height="600" loading="lazy">
						<div class="recent-work-vertical card-img-overlay d-flex align-items-end">
							<div class="recent-work-content text-start mb-3 ml-3 text-dark">
								<h3 class="card-title light-300"><?php the_title(); ?></h3>
								<p class="card-text"><?php echo wp_kses_post( get_the_excerpt() ); ?></p>
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
</section>
<!-- End Recent Work -->
