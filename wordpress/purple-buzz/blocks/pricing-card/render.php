<?php
/**
 * Server side render for the Pricing Card block.
 *
 * @package Purple_Buzz
 *
 * @param array $attributes Block attributes.
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

$plan_name     = isset( $attributes['planName'] ) ? $attributes['planName'] : '';
$price         = isset( $attributes['price'] ) ? $attributes['price'] : '';
$period        = isset( $attributes['period'] ) ? $attributes['period'] : '';
$features      = isset( $attributes['features'] ) && is_array( $attributes['features'] ) ? $attributes['features'] : array();
$highlighted   = ! empty( $attributes['highlighted'] );
$button_label  = isset( $attributes['buttonLabel'] ) ? $attributes['buttonLabel'] : '';
$button_url    = isset( $attributes['buttonUrl'] ) ? $attributes['buttonUrl'] : '';
$features_text = array_filter( array_map( 'trim', $features ) );
?>
<div class="col-md-4 pb-5 pt-sm-0 mt-5 px-xl-3">
	<div class="pricing-table card h-100 <?php echo $highlighted ? 'bg-secondary card-rounded' : ''; ?> shadow-sm border-0 py-5">
		<div class="pricing-table-body card-body <?php echo $highlighted ? 'text-white' : 'rounded-pill'; ?> text-center align-self-center p-md-0">
			<i class="pricing-table-icon display-3 bx bx-package <?php echo $highlighted ? 'text-white' : 'text-secondary'; ?>"></i>
			<h3 class="pricing-table-heading h5 semi-bold-600"><?php echo esc_html( $plan_name ); ?></h3>
			<p><?php echo esc_html( $price . $period ); ?></p>

			<?php if ( $features_text ) : ?>
				<ul class="pricing-table-body text-start text-dark px-4 list-unstyled light-300">
					<?php foreach ( $features_text as $pb_feature ) : ?>
						<li class="<?php echo $highlighted ? 'text-white' : ''; ?>">
							<i class="bx bxs-circle me-2"></i><?php echo esc_html( $pb_feature ); ?>
						</li>
					<?php endforeach; ?>
				</ul>
			<?php endif; ?>

			<div class="pricing-table-footer pt-5">
				<?php if ( $button_label && $button_url ) : ?>
					<a href="<?php echo esc_url( $button_url ); ?>" class="btn rounded-pill px-4 <?php echo $highlighted ? 'btn-outline-light' : 'btn-outline-primary'; ?> light-300">
						<?php echo esc_html( $button_label ); ?>
					</a>
				<?php endif; ?>
			</div>
		</div>
	</div>
</div>
