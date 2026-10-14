<?php
/**
 * No results message.
 *
 * @package Purple_Buzz
 */
?>
<section class="container py-5">
	<div class="row justify-content-center text-center py-5">
		<div class="col-lg-8">
			<h2 class="h3 semi-bold-600 pb-3"><?php esc_html_e( 'Nothing here', 'purple-buzz' ); ?></h2>
			<p class="light-300 text-muted">
				<?php esc_html_e( 'It looks like nothing was found at this location. Try a search?', 'purple-buzz' ); ?>
			</p>
			<?php get_search_form(); ?>
		</div>
	</div>
</section>
