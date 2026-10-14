<?php
/**
 * Service card — the overlay card used by the home services grid.
 *
 * @package Purple_Buzz
 */

$pb_terms   = get_the_terms( get_the_ID(), 'service_category' );
$pb_classes = array( 'project' );
$pb_label   = get_the_title();
if ( ! is_wp_error( $pb_terms ) && $pb_terms ) {
	foreach ( $pb_terms as $pb_term ) {
		$pb_classes[] = 'term-' . $pb_term->slug;
	}
	$pb_label = $pb_terms[0]->name;
}
?>


<div class="col-xl-3 col-md-4 col-sm-6 <?php echo esc_attr( implode( ' ', $pb_classes ) ); ?>">
	<a href="<?php the_permalink(); ?>" class="service-work card border-0 text-white shadow-sm overflow-hidden mx-5 m-sm-0">
		<img class="service card-img" src="<?php echo esc_url( purple_buzz_thumbnail_url() ); ?>" alt="<?php the_title_attribute(); ?>" loading="lazy">
		<div class="service-work-vertical card-img-overlay d-flex align-items-end">
			<div class="service-work-content text-left text-light">
				<span class="btn btn-outline-light rounded-pill mb-lg-3 px-lg-4 light-300"><?php echo esc_html( $pb_label ); ?></span>
				<p class="card-text"><?php echo wp_kses_post( get_the_excerpt() ); ?></p>
			</div>
		</div>
	</a>
</div>