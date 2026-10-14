<?php
/**
 * Home hero carousel.
 *
 * @package Purple_Buzz
 */

$pb_slides = array(
	array(
		'heading' => 'Develop <strong>Strategies</strong> for <br>your business',
		'body'    => get_bloginfo( 'description' ),
		'label'   => __( 'Get Started', 'purple-buzz' ),
		'url'     => purple_buzz_page_url( 'page-templates/template-contact.php' ),
	),
	array(
		'heading' => __( 'Services built around <strong>your</strong> <br>goals', 'purple-buzz' ),
		'body'    => __( 'From brand and design to digital marketing, we plan and ship the work that moves your business forward.', 'purple-buzz' ),
		'label'   => __( 'Our Services', 'purple-buzz' ),
		'url'     => get_post_type_archive_link( 'services' ),
	),
	array(
		'heading' => __( 'Let\'s build something <strong>worth</strong> <br>talking about', 'purple-buzz' ),
		'body'    => __( 'Tell us about your project and we will come back with a plan, a timeline and a straight answer.', 'purple-buzz' ),
		'label'   => __( 'Contact Us', 'purple-buzz' ),
		'url'     => purple_buzz_page_url( 'page-templates/template-contact.php' ),
	),
);
?>
<!-- Start Banner Hero -->
<div class="banner-wrapper bg-light">
	<div id="index_banner" class="banner-vertical-center-index container-fluid pt-5">

		<div id="carouselExampleIndicators" class="carousel slide" data-bs-ride="carousel">
			<ol class="carousel-indicators">
				<?php foreach ( $pb_slides as $pb_index => $pb_slide ) : ?>
					<li data-bs-target="#carouselExampleIndicators" data-bs-slide-to="<?php echo esc_attr( $pb_index ); ?>" class="<?php echo 0 === $pb_index ? 'active' : ''; ?>"></li>
				<?php endforeach; ?>
			</ol>
			<div class="carousel-inner">
				<?php foreach ( $pb_slides as $pb_index => $pb_slide ) : ?>
					<div class="carousel-item <?php echo 0 === $pb_index ? 'active' : ''; ?>">
						<div class="py-5 row d-flex align-items-center">
							<div class="banner-content col-lg-8 col-8 offset-2 m-lg-auto text-left py-5 pb-5">
								<h2 class="banner-heading h1 text-secondary display-3 mb-0 pb-5 mx-0 px-0 light-300 typo-space-line">
									<?php echo wp_kses_post( $pb_slide['heading'] ); ?>
								</h2>
								<p class="banner-body text-muted py-3 mx-0 px-0">
									<?php echo wp_kses_post( $pb_slide['body'] ); ?>
								</p>
								<a class="banner-button btn rounded-pill btn-outline-primary btn-lg px-4" href="<?php echo esc_url( $pb_slide['url'] ); ?>" role="button">
									<?php echo esc_html( $pb_slide['label'] ); ?>
								</a>
							</div>
						</div>
					</div>
				<?php endforeach; ?>
			</div>
			<a class="carousel-control-prev text-decoration-none" href="#carouselExampleIndicators" role="button" data-bs-slide="prev">
				<i class="bx bx-chevron-left"></i>
				<span class="visually-hidden"><?php esc_html_e( 'Previous', 'purple-buzz' ); ?></span>
			</a>
			<a class="carousel-control-next text-decoration-none" href="#carouselExampleIndicators" role="button" data-bs-slide="next">
				<i class="bx bx-chevron-right"></i>
				<span class="visually-hidden"><?php esc_html_e( 'Next', 'purple-buzz' ); ?></span>
			</a>
		</div>

	</div>
</div>
<!-- End Banner Hero -->
