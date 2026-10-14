<?php
/**
 * Team member card.
 *
 * @package Purple_Buzz
 */

$pb_position = get_post_meta( get_the_ID(), 'pb_position', true );
?>
<div <?php post_class( 'team-member col-md-4' ); ?>>
	<a href="<?php the_permalink(); ?>" class="text-decoration-none">
		<img class="team-member-img img-fluid rounded-circle p-4" src="<?php echo esc_url( purple_buzz_thumbnail_url( get_the_ID(), 'purple-buzz-portrait' ) ); ?>" alt="<?php the_title_attribute(); ?>" width="480" height="480" loading="lazy">
		<ul class="team-member-caption list-unstyled text-center pt-4 text-muted light-300">
			<li><?php the_title(); ?></li>
			<?php if ( $pb_position ) : ?>
				<li><?php echo esc_html( $pb_position ); ?></li>
			<?php endif; ?>
		</ul>
	</a>
</div>
