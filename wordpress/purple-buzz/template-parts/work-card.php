<?php
/**
 * Work card — used by the work archive, home and related sections.
 *
 * @package Purple_Buzz
 */

$pb_terms    = get_the_terms( get_the_ID(), 'work_category' );
$pb_classes  = array( 'project' );
if ( ! is_wp_error( $pb_terms ) && $pb_terms ) {
	foreach ( $pb_terms as $pb_term ) {
		$pb_classes[] = 'term-' . $pb_term->slug;
	}
}
?>
<div class="col-sm-6 col-lg-4 text-decoration-none <?php echo esc_attr( implode( ' ', $pb_classes ) ); ?>">
	<a href="<?php the_permalink(); ?>" class="service-work overflow-hidden card mb-5 mx-5 m-sm-0 text-decoration-none">
		<img class="card-img-top" src="<?php echo esc_url( purple_buzz_thumbnail_url() ); ?>" alt="<?php the_title_attribute(); ?>" width="800" height="600" loading="lazy">
		<div class="card-body">
			<h3 class="card-title h5 light-300 text-dark"><?php the_title(); ?></h3>
			<p class="card-text light-300 text-dark">
				<?php echo wp_kses_post( get_the_excerpt() ); ?>
			</p>
			<span class="text-decoration-none text-primary light-300">
				<?php esc_html_e( 'Read more', 'purple-buzz' ); ?> <i class="bx bxs-hand-right ms-1"></i>
			</span>
		</div>
	</a>
</div>
