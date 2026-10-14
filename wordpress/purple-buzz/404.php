<?php
/**
 * 404 template.
 *
 * @package Purple_Buzz
 */

get_header();

purple_buzz_page_banner( __( 'The page you were looking for could not be found.', 'purple-buzz' ), __( '404 — Page not found', 'purple-buzz' ) );
?>

<main id="primary" class="site-main">
	<section class="container py-5">
		<div class="row justify-content-center text-center py-5">
			<div class="col-lg-7">
				<p class="display-6 pb-4 text-muted light-300">
					<?php esc_html_e( 'Maybe it moved, maybe the link is broken. Try a search instead.', 'purple-buzz' ); ?>
				</p>
				<?php get_search_form(); ?>
				<p class="pt-4">
					<a class="btn rounded-pill btn-outline-primary px-4" href="<?php echo esc_url( home_url( '/' ) ); ?>">
						<?php esc_html_e( 'Back to home', 'purple-buzz' ); ?>
					</a>
				</p>
			</div>
		</div>
	</section>
</main>

<?php
get_footer();
