<?php
/**
 * Archive template: work, services, team and default archives.
 *
 * @package Purple_Buzz
 */

get_header();

// Resolve the content type before the loop: query vars are available, the
// global post is not.
$pb_type = 'post';
if ( is_post_type_archive() ) {
	$pb_type = get_query_var( 'post_type' );
	$pb_type = is_array( $pb_type ) ? reset( $pb_type ) : $pb_type;
} elseif ( is_tax() ) {
	$pb_taxonomy = get_query_var( 'taxonomy' );
	if ( 'work_category' === $pb_taxonomy ) {
		$pb_type = 'work';
	} elseif ( 'service_category' === $pb_taxonomy ) {
		$pb_type = 'services';
	}
}

purple_buzz_page_banner();
?>

<main id="primary" class="site-main">

	<?php if ( 'work' === $pb_type || 'services' === $pb_type ) : ?>

		<?php
		$pb_tax   = 'work' === $pb_type ? 'work_category' : 'service_category';
		$pb_terms = get_terms(
			array(
				'taxonomy'   => $pb_tax,
				'hide_empty' => true,
			)
		);
		?>
		<section class="container py-5">

			<?php if ( ! is_wp_error( $pb_terms ) && $pb_terms ) : ?>
				<div class="row justify-content-center my-5">
					<div class="filter-btns shadow-md rounded-pill text-center col-auto">
						<a class="filter-btn btn rounded-pill btn-outline-primary border-0 m-md-2 px-md-4 active" data-filter=".project" href="#"><?php esc_html_e( 'All', 'purple-buzz' ); ?></a>
						<?php foreach ( $pb_terms as $pb_term ) : ?>
							<a class="filter-btn btn rounded-pill btn-outline-primary border-0 m-md-2 px-md-4" data-filter=".term-<?php echo esc_attr( $pb_term->slug ); ?>" href="#">
								<?php echo esc_html( $pb_term->name ); ?>
							</a>
						<?php endforeach; ?>
					</div>
				</div>
			<?php endif; ?>

			<?php if ( have_posts() ) : ?>
				<div class="row projects gx-lg-5">
					<?php
					while ( have_posts() ) {
						the_post();
						if ( 'services' === $pb_type ) {
							get_template_part( 'template-parts/service', 'card' );
						} else {
							get_template_part( 'template-parts/work', 'card' );
						}
					}
					?>
				</div>
				<?php purple_buzz_pagination(); ?>
			<?php else : ?>
				<?php get_template_part( 'template-parts/content', 'none' ); ?>
			<?php endif; ?>

		</section>

	<?php elseif ( 'team' === $pb_type ) : ?>

		<section class="container py-5">
			<?php if ( have_posts() ) : ?>
				<div class="row py-5">
					<?php
					while ( have_posts() ) {
						the_post();
						get_template_part( 'template-parts/team', 'card' );
					}
					?>
				</div>
				<?php purple_buzz_pagination(); ?>
			<?php else : ?>
				<?php get_template_part( 'template-parts/content', 'none' ); ?>
			<?php endif; ?>
		</section>

	<?php else : ?>

		<section class="container py-5">
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

	<?php endif; ?>

</main>

<?php
get_footer();
