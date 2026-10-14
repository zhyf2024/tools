<?php
/**
 * Server side render for the CTA Banner block.
 *
 * @package Purple_Buzz
 *
 * @param array $attributes Block attributes.
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

$heading      = isset( $attributes['heading'] ) ? $attributes['heading'] : '';
$text         = isset( $attributes['text'] ) ? $attributes['text'] : '';
$icon         = isset( $attributes['icon'] ) && $attributes['icon'] ? $attributes['icon'] : 'bxs-box';
$button_label = isset( $attributes['buttonLabel'] ) ? $attributes['buttonLabel'] : '';
$button_url   = isset( $attributes['buttonUrl'] ) ? $attributes['buttonUrl'] : '';
?>
<section class="bg-secondary">
	<div class="container py-5">
		<div class="row d-flex justify-content-center text-center">
			<div class="col-lg-2 col-12 text-light align-items-center">
				<i class="display-1 bx <?php echo esc_attr( $icon ); ?> bx-lg"></i>
			</div>
			<div class="col-lg-7 col-12 text-light pt-2">
				<?php if ( $heading ) : ?>
					<h3 class="h4 light-300"><?php echo wp_kses_post( $heading ); ?></h3>
				<?php endif; ?>
				<?php if ( $text ) : ?>
					<p class="light-300"><?php echo wp_kses_post( $text ); ?></p>
				<?php endif; ?>
			</div>
			<div class="col-lg-3 col-12 pt-4">
				<?php if ( $button_label && $button_url ) : ?>
					<a href="<?php echo esc_url( $button_url ); ?>" class="btn btn-primary rounded-pill btn-block shadow px-4 py-2">
						<?php echo esc_html( $button_label ); ?>
					</a>
				<?php endif; ?>
			</div>
		</div>
	</div>
</section>
