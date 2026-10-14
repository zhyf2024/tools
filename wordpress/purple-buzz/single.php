<?php
/**
 * Single post, service or team member.
 *
 * @package Purple_Buzz
 */

get_header();

while ( have_posts() ) {
	the_post();

	$pb_subtitle = get_post_meta( get_the_ID(), 'pb_subtitle', true );
	if ( ! $pb_subtitle && 'post' === get_post_type() ) {
		$pb_subtitle = get_the_date();
	}

	purple_buzz_page_banner( $pb_subtitle );
	?>

	<main id="primary" class="site-main">
		<section class="container py-5">
			<div class="row pt-5">
				<div class="worksingle-content col-lg-8 m-auto text-left justify-content-center">

					<?php if ( 'team' === get_post_type() ) : ?>
						<div class="text-center pb-4">
							<img class="team-member-img img-fluid rounded-circle p-4" src="<?php echo esc_url( purple_buzz_thumbnail_url( get_the_ID(), 'purple-buzz-portrait' ) ); ?>" alt="<?php the_title_attribute(); ?>" width="480" height="480">
							<?php $pb_position = get_post_meta( get_the_ID(), 'pb_position', true ); ?>
							<?php if ( $pb_position ) : ?>
								<p class="text-muted light-300 mb-0"><?php echo esc_html( $pb_position ); ?></p>
							<?php endif; ?>
						</div>
					<?php endif; ?>

					<?php if ( has_post_thumbnail() && 'team' !== get_post_type() ) : ?>
						<div class="pb-4">
							<img class="img-fluid border rounded" src="<?php echo esc_url( get_the_post_thumbnail_url( get_the_ID(), 'large' ) ); ?>" alt="<?php the_title_attribute(); ?>">
						</div>
					<?php endif; ?>

					<div class="entry-content light-300 text-muted">
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

					<?php if ( 'post' === get_post_type() ) : ?>
						<footer class="entry-footer pt-4 light-300">
							<?php
							purple_buzz_posted_on();
							echo '<br>';
							purple_buzz_entry_footer();
							?>
						</footer>
					<?php endif; ?>
				</div>
			</div>
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
	</main>

	<?php
}

get_footer();
