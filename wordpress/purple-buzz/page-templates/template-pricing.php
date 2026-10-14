<?php
/**
 * Template Name: Pricing
 *
 * @package Purple_Buzz
 */

get_header();
?>

<main id="primary" class="site-main">

	<?php
	while ( have_posts() ) {
		the_post();
		?>

		<!-- Start Pricing Header -->
		<div class="container-lg py-5">
			<div class="col-md-12 m-auto text-center py-5">
				<h1 class="pricing-header h2 semi-bold-600"><?php the_title(); ?></h1>
				<p class="pricing-footer">
					<?php echo wp_kses_post( get_the_excerpt() ? get_the_excerpt() : __( 'Consectetur adipiscing elit, sed do eiusmod tempor incididunt ut facilisis.', 'purple-buzz' ) ); ?>
				</p>
			</div>

			<?php if ( trim( get_the_content() ) ) : ?>
				<div class="row pb-4">
					<div class="col-lg-10 mx-auto">
						<?php the_content(); ?>
					</div>
				</div>
			<?php endif; ?>
		<?php
	}
	?>

		<div class="row px-lg-3">

			<?php
			$pb_plans = array(
				array(
					'title'  => __( 'Free Plan', 'purple-buzz' ),
					'price'  => '$0',
					'period' => '',
					'feat'   => array( '5 Users', '2 TB space', 'Community Forums', 'Email Support' ),
					'dark'  => false,
				),
				array(
					'title'  => __( 'Standard Plan', 'purple-buzz' ),
					'price'  => '$120',
					'period' => '/Year',
					'feat'   => array( '25 to 99 Users', '10 TB space', 'Source Files', 'Live Chat' ),
					'dark'  => true,
				),
				array(
					'title'  => __( 'Enterprise', 'purple-buzz' ),
					'price'  => '$840',
					'period' => '/Year',
					'feat'   => array( '100 users or more', '80 TB space', 'Full Access Sources', 'Live Chat', 'Customizations' ),
					'dark'  => false,
				),
			);

			foreach ( $pb_plans as $pb_index => $pb_plan ) :
				$pb_offset = $pb_plan['dark'] ? '' : 'pb-5 pt-sm-0 mt-5';
				?>
				<div class="col-md-4 <?php echo esc_attr( $pb_offset ); ?> px-xl-3">
					<div class="pricing-table card h-100 <?php echo $pb_plan['dark'] ? 'bg-secondary card-rounded' : ''; ?> shadow-sm border-0 py-5">
						<div class="pricing-table-body card-body <?php echo $pb_plan['dark'] ? 'text-white' : 'rounded-pill'; ?> text-center align-self-center p-md-0">
							<i class="pricing-table-icon display-3 bx bx-package <?php echo $pb_plan['dark'] ? 'text-white' : 'text-secondary'; ?>"></i>
							<h2 class="pricing-table-heading h5 semi-bold-600"><?php echo esc_html( $pb_plan['title'] ); ?></h2>
							<p><?php echo esc_html( $pb_plan['price'] . $pb_plan['period'] ); ?></p>
							<ul class="pricing-table-body text-start text-dark px-4 list-unstyled light-300">
								<?php foreach ( $pb_plan['feat'] as $pb_feature ) : ?>
									<li class="<?php echo $pb_plan['dark'] ? 'text-white' : ''; ?>"><i class="bx bxs-circle me-2"></i><?php echo esc_html( $pb_feature ); ?></li>
								<?php endforeach; ?>
							</ul>
							<div class="pricing-table-footer pt-5">
								<a href="<?php echo esc_url( purple_buzz_page_url( 'page-templates/template-contact.php' ) ); ?>" class="btn rounded-pill px-4 <?php echo $pb_plan['dark'] ? 'btn-outline-light' : 'btn-outline-primary'; ?> light-300">
									<?php esc_html_e( 'Get Now', 'purple-buzz' ); ?>
								</a>
							</div>
						</div>
					</div>
				</div>
			<?php endforeach; ?>

		</div>
	</div>
	<!-- End Content -->

	<!-- Start Pricing Horizontal Section -->
	<section class="bg-light pt-sm-0 py-5">
		<div class="container py-5">

			<h2 class="h2 semi-bold-600 text-center mt-2"><?php esc_html_e( 'Our Pricing', 'purple-buzz' ); ?></h2>
			<p class="text-center pb-5 light-300"><?php esc_html_e( 'Consectetur adipiscing elit, sed do eiusmod tempor incididunt ut facilisis.', 'purple-buzz' ); ?></p>

			<?php foreach ( $pb_plans as $pb_index => $pb_plan ) : ?>
				<div class="pricing-horizontal row col-10 m-auto d-flex shadow-sm rounded overflow-hidden <?php echo 1 === $pb_index ? 'my-5 ' : ''; ?>bg-white">
					<div class="pricing-horizontal-icon col-md-3 text-center bg-secondary text-light py-4">
						<i class="display-1 bx bx-package pt-4"></i>
						<h3 class="h5 semi-bold-600 pb-4 light-300"><?php echo esc_html( $pb_plan['title'] ); ?></h3>
					</div>
					<div class="pricing-horizontal-body offset-lg-1 col-md-5 col-lg-4 d-flex align-items-center pl-5 pt-lg-0 pt-4">
						<ul class="text-left px-4 list-unstyled mb-0 light-300">
							<?php foreach ( array_slice( $pb_plan['feat'], 0, 4 ) as $pb_feature ) : ?>
								<li><i class="bx bxs-circle me-2"></i><?php echo esc_html( $pb_feature ); ?></li>
							<?php endforeach; ?>
						</ul>
					</div>
					<div class="pricing-horizontal-tag col-md-4 text-center pt-3 d-flex align-items-center">
						<div class="w-100 light-300">
							<p><?php echo esc_html( $pb_plan['price'] . $pb_plan['period'] ); ?></p>
							<a href="<?php echo esc_url( purple_buzz_page_url( 'page-templates/template-contact.php' ) ); ?>" class="btn rounded-pill px-4 btn-outline-primary mb-3">
								<?php esc_html_e( 'Get Now', 'purple-buzz' ); ?>
							</a>
						</div>
					</div>
				</div>
			<?php endforeach; ?>

		</div>
	</section>
	<!-- End Pricing Horizontal Section -->

	<section class="container py-5">

		<h2 class="h2 semi-bold-600 text-center pt-5"><?php esc_html_e( 'Pricing', 'purple-buzz' ); ?></h2>
		<p class="text-center pb-5 light-300">
			<?php esc_html_e( 'Consectetur adipiscing elit, sed do eiusmod tempor incididunt ut facilisis.', 'purple-buzz' ); ?>
		</p>

		<div class="row d-flex align-items-center pb-5">

			<div class="col-lg-6 offset-lg-0 col-md-8 offset-md-2">
				<img class="rounded float-end" src="<?php echo esc_url( PURPLE_BUZZ_URI . '/assets/img/pricing.svg' ); ?>" alt="" width="540" height="420" loading="lazy">
			</div>

			<div class="col-lg-6">

				<?php foreach ( $pb_plans as $pb_index => $pb_plan ) : ?>
					<div class="pricing-list shadow-sm <?php echo 0 === $pb_index ? 'rounded-top' : ( 2 === $pb_index ? 'rounded-bottom' : '' ); ?> rounded-3 py-sm-0 py-5">
						<div class="row p-2">
							<div class="pricing-list-icon col-3 text-center m-auto text-secondary ml-5 py-2">
								<i class="display-3 bx bx-package"></i>
							</div>
							<div class="pricing-list-body col-md-5 align-items-center pl-3 pt-2">
								<ul class="list-unstyled text-center light-300">
									<li class="h5 semi-bold-600 mb-0 mt-3"><?php echo esc_html( $pb_plan['title'] ); ?></li>
									<li><?php echo esc_html( $pb_plan['feat'][ count( $pb_plan['feat'] ) - 1 ] ); ?></li>
								</ul>
							</div>
							<div class="pricing-list-footer col-4 text-center m-auto align-items-center">
								<a href="<?php echo esc_url( purple_buzz_page_url( 'page-templates/template-contact.php' ) ); ?>" class="btn rounded-pill px-4 btn-primary light-300">
									<?php echo esc_html( $pb_plan['price'] . $pb_plan['period'] ); ?>
								</a>
							</div>
						</div>
					</div>
				<?php endforeach; ?>

				<p class="text-center">
					<a class="btn px-4 mt-4 mx-auto btn-outline-primary" href="<?php echo esc_url( purple_buzz_page_url( 'page-templates/template-contact.php' ) ); ?>">
						<?php esc_html_e( 'Get Now', 'purple-buzz' ); ?>
					</a>
				</p>

			</div>
		</div>
	</section>

</main>

<?php
get_footer();
