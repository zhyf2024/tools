<?php
/**
 * Blog index / posts page.
 *
 * @package Purple_Buzz
 */

get_header();

purple_buzz_page_banner(
	__( 'News, notes and case studies from the studio.', 'purple-buzz' ),
	is_home() ? get_bloginfo( 'name' ) : null
);
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
