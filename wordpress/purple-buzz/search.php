<?php
/**
 * Search results.
 *
 * @package Purple_Buzz
 */

get_header();

/* translators: %s: search query. */
$pb_subtitle = sprintf( __( 'Results for “%s”', 'purple-buzz' ), get_search_query() );

purple_buzz_page_banner( $pb_subtitle, __( 'Search', 'purple-buzz' ) );
?>

<main id="primary" class="site-main">
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
</main>

<?php
get_footer();
