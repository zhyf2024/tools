<?php
/**
 * Post card used by the blog index, search and category archives.
 *
 * @package Purple_Buzz
 */
?>
<div <?php post_class( 'col-md-4 mb-4' ); ?>>
	<a href="<?php the_permalink(); ?>" class="related-content card text-decoration-none overflow-hidden h-100 shadow-sm">
		<?php if ( has_post_thumbnail() ) : ?>
			<img class="related-img card-img-top" src="<?php echo esc_url( get_the_post_thumbnail_url( get_the_ID(), 'purple-buzz-card' ) ); ?>" alt="<?php the_title_attribute(); ?>" width="800" height="600">
		<?php endif; ?>
		<div class="related-body card-body p-4">
			<h3 class="card-title h6 m-0 semi-bold-600 text-dark"><?php the_title(); ?></h3>
			<p class="card-text pt-2 mb-1 light-300 text-dark">
				<?php echo wp_kses_post( get_the_excerpt() ); ?>
			</p>
			<div class="d-flex justify-content-between pt-2">
				<span class="text-primary light-300"><?php esc_html_e( 'Read more', 'purple-buzz' ); ?></span>
				<span class="light-300 text-muted"><?php echo esc_html( get_the_date() ); ?></span>
			</div>
		</div>
	</a>
</div>
