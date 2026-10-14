<?php
/**
 * Home services section with the isotope category filter.
 *
 * @package Purple_Buzz
 */

$pb_services = new WP_Query(
	array(
		'post_type'      => 'services',
		'posts_per_page' => 12,
		'no_found_rows'  => true,
	)
);

if ( ! $pb_services->have_posts() ) {
	return;
}

$pb_terms = get_terms(
	array(
		'taxonomy'   => 'service_category',
		'hide_empty' => true,
	)
);
?>
<!-- Start Service -->
<section class="service-wrapper py-3">
	<div class="container-fluid pb-3">
		<div class="row">
			<h2 class="h2 text-center col-12 py-5 semi-bold-600"><?php esc_html_e( 'Services', 'purple-buzz' ); ?></h2>
			<div class="service-header col-2 col-lg-3 text-end light-300">
				<i class="bx bx-gift h3 mt-1"></i>
			</div>
			<div class="service-heading col-10 col-lg-9 text-start float-end light-300">
				<h3 class="h3 pb-4 typo-space-line"><?php esc_html_e( 'Make Success for future', 'purple-buzz' ); ?></h3>
			</div>
		</div>
		<p class="service-footer col-10 offset-2 col-lg-9 offset-lg-3 text-start pb-3 text-muted px-2">
			<?php esc_html_e( 'A short line describing what your team does best. Edit this text in the services section of the home template.', 'purple-buzz' ); ?>
		</p>
	</div>

	<?php if ( ! is_wp_error( $pb_terms ) && $pb_terms ) : ?>
		<div class="service-tag py-5 bg-secondary">
			<div class="col-md-12">
				<ul class="nav d-flex justify-content-center">
					<li class="nav-item mx-lg-4">
						<a class="filter-btn nav-link btn-outline-primary active shadow rounded-pill text-light px-4 light-300" href="#" data-filter=".project"><?php esc_html_e( 'All', 'purple-buzz' ); ?></a>
					</li>
					<?php foreach ( $pb_terms as $pb_term ) : ?>
						<li class="nav-item mx-lg-4">
							<a class="filter-btn nav-link btn-outline-primary rounded-pill text-light px-4 light-300" href="#" data-filter=".term-<?php echo esc_attr( $pb_term->slug ); ?>">
								<?php echo esc_html( $pb_term->name ); ?>
							</a>
						</li>
					<?php endforeach; ?>
				</ul>
			</div>
		</div>
	<?php endif; ?>
</section>

<section class="container overflow-hidden py-5">
	<div class="row gx-5 gx-sm-3 gx-lg-5 gy-lg-5 gy-3 pb-3 projects">
		<?php
		while ( $pb_services->have_posts() ) {
			$pb_services->the_post();
			get_template_part( 'template-parts/service', 'card' );
		}
		wp_reset_postdata();
		?>
	</div>
</section>
<!-- End Service -->
