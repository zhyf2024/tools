<?php
/**
 * Template Name: About
 *
 * @package Purple_Buzz
 */

get_header();

$pb_members = new WP_Query(
	array(
		'post_type'      => 'team',
		'posts_per_page' => 6,
		'no_found_rows'  => true,
	)
);
?>

<main id="primary" class="site-main">

	<?php
	while ( have_posts() ) {
		the_post();
		?>

		<!-- Start Banner Hero -->
		<section class="bg-light w-100">
			<div class="container">
				<div class="row d-flex align-items-center py-5">
					<div class="col-lg-6 text-start">
						<h1 class="h2 py-5 text-primary typo-space-line"><?php the_title(); ?></h1>
						<p class="light-300">
							<?php echo wp_kses_post( get_the_excerpt() ? get_the_excerpt() : get_bloginfo( 'description' ) ); ?>
						</p>
					</div>
					<div class="col-lg-6">
						<img src="<?php echo esc_url( PURPLE_BUZZ_URI . '/assets/img/banner-img-02.svg' ); ?>" alt="" width="600" height="400" loading="lazy">
					</div>
				</div>
			</div>
		</section>
		<!-- End Banner Hero -->

		<?php if ( trim( get_the_content() ) ) : ?>
			<section class="container py-5">
				<div class="row">
					<div class="col-lg-10 mx-auto">
						<?php the_content(); ?>
					</div>
				</div>
			</section>
		<?php endif; ?>

		<?php
	}
	?>

	<?php if ( $pb_members->have_posts() ) : ?>
		<!-- Start Team Member -->
		<section class="container py-5">
			<div class="pt-5 pb-3 d-lg-flex align-items-center gx-5">

				<div class="col-lg-3">
					<h2 class="h2 py-5 typo-space-line"><?php esc_html_e( 'Our Team', 'purple-buzz' ); ?></h2>
					<p class="text-muted light-300">
						<?php esc_html_e( 'The people behind the work — add members under Team in the dashboard.', 'purple-buzz' ); ?>
					</p>
				</div>

				<div class="col-lg-9 row">
					<?php
					while ( $pb_members->have_posts() ) {
						$pb_members->the_post();
						get_template_part( 'template-parts/team', 'card' );
					}
					wp_reset_postdata();
					?>
				</div>

			</div>
		</section>
		<!-- End Team Member -->
	<?php endif; ?>

	<!-- Start Our Partner -->
	<section class="bg-secondary py-3">
		<div class="container py-5">
			<h2 class="h2 text-white text-center py-5"><?php esc_html_e( 'Our Partner', 'purple-buzz' ); ?></h2>
			<div class="row text-center">
				<?php
				$pb_partners = array(
					'bxs-buildings',
					'bxs-check-shield',
					'bxs-bolt-circle',
					'bxs-spa',
				);
				foreach ( $pb_partners as $pb_partner ) :
					?>
					<div class="col-md-3 mb-3">
						<div class="card partner-wap py-5">
							<span aria-hidden="true"><i class="display-1 text-white bx <?php echo esc_attr( $pb_partner ); ?>"></i></span>
						</div>
					</div>
				<?php endforeach; ?>
			</div>
		</div>
	</section>
	<!-- End Our Partner -->

	<!-- Start Progress -->
	<section class="bg-white py-5">
		<div class="container my-4">

			<h2 class="creative-heading h2 pb-3"><?php esc_html_e( 'Creative & Make Perfect', 'purple-buzz' ); ?></h2>

			<div class="creative-content row py-3">
				<div class="col-md-5">
					<p class="text-muted col-lg-8 light-300">
						<?php esc_html_e( 'Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.', 'purple-buzz' ); ?>
					</p>
				</div>
				<div class="creative-progress col-md-7">

					<?php
					$pb_skills = array(
						__( 'Development', 'purple-buzz' ) => 66,
						__( 'Design', 'purple-buzz' )      => 90,
						__( 'Marketing', 'purple-buzz' )   => 74,
					);
					foreach ( $pb_skills as $pb_skill => $pb_percent ) :
						?>
						<div class="row mt-4 mt-sm-2">
							<div class="col-6">
								<h3 class="h5"><?php echo esc_html( $pb_skill ); ?></h3>
							</div>
							<div class="col-6 text-end"><?php echo esc_html( $pb_percent ); ?>%</div>
						</div>
						<div class="progress">
							<div class="progress-bar" role="progressbar" style="width: <?php echo esc_attr( $pb_percent ); ?>%" aria-valuenow="<?php echo esc_attr( $pb_percent ); ?>" aria-valuemin="0" aria-valuemax="100"></div>
						</div>
					<?php endforeach; ?>

				</div>
			</div>
		</div>
	</section>
	<!-- End Progress -->

	<!-- Start Choice -->
	<section class="why-us banner-bg bg-light">
		<div class="container my-4">
			<div class="row">
				<div class="banner-img col-lg-5">
					<img src="<?php echo esc_url( PURPLE_BUZZ_URI . '/assets/img/work.svg' ); ?>" class="rounded img-fluid" alt="" width="540" height="360" loading="lazy">
				</div>
				<div class="banner-content col-lg-7 align-self-end">
					<h2 class="h2 pb-3"><?php esc_html_e( 'Why you choose us?', 'purple-buzz' ); ?></h2>
					<p class="text-muted pb-5 light-300">
						<?php esc_html_e( 'Straight answers, shipped work and no surprises — we treat your budget like it is our own.', 'purple-buzz' ); ?>
					</p>
				</div>
			</div>
		</div>
	</section>
	<!-- End Choice -->

	<!-- Start Aim -->
	<section class="banner-bg bg-white py-5">
		<div class="container my-4">
			<div class="row text-center">

				<?php
				$pb_objectives = array(
					array(
						'icon'    => 'bxs-bulb',
						'title'   => __( 'Our Vision', 'purple-buzz' ),
						'text'    => __( 'Incididunt ut labore et dolore magna aliqua. Quis ipsum suspendisse commodo viverra.', 'purple-buzz' ),
					),
					array(
						'icon'    => 'bx-revision',
						'title'   => __( 'Our Mission', 'purple-buzz' ),
						'text'    => __( 'Eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam quis.', 'purple-buzz' ),
					),
					array(
						'icon'    => 'bxs-select-multiple',
						'title'   => __( 'Our Goal', 'purple-buzz' ),
						'text'    => __( 'Lorem ipsum dolor sit amet, consectetur adipisicing elit, sed do eiusmod tempor.', 'purple-buzz' ),
					),
				);
				foreach ( $pb_objectives as $pb_index => $pb_objective ) :
					?>
					<div class="objective col-lg-4 <?php echo 0 === $pb_index ? '' : 'mt-sm-0 mt-4'; ?>">
						<div class="objective-icon card m-auto py-4 mb-2 mb-sm-4 bg-secondary shadow-lg">
							<i class="display-4 bx <?php echo esc_attr( $pb_objective['icon'] ); ?> text-light"></i>
						</div>
						<h3 class="objective-heading h3 mb-2 mb-sm-4 light-300"><?php echo esc_html( $pb_objective['title'] ); ?></h3>
						<p class="light-300"><?php echo esc_html( $pb_objective['text'] ); ?></p>
					</div>
				<?php endforeach; ?>

			</div>
		</div>
	</section>
	<!-- End Aim -->

	<!-- Start Contact -->
	<section class="banner-bg bg-light py-5">
		<div class="container">
			<div class="row">
			<div class="col-lg-6 mx-auto my-4 p-3">
				<?php purple_buzz_contact_notice(); ?>
				<form action="<?php echo esc_url( admin_url( 'admin-post.php' ) ); ?>" method="post">
						<h2 class="h2 text-center"><?php esc_html_e( 'Stay up to date with us', 'purple-buzz' ); ?></h2>
						<input type="hidden" name="action" value="pb_subscribe">
						<?php wp_nonce_field( 'pb_subscribe', 'pb_subscribe_nonce' ); ?>
						<div class="input-group py-3">
							<label class="screen-reader-text" for="pb_subscribe_email"><?php esc_html_e( 'Your Email', 'purple-buzz' ); ?></label>
							<input name="pb_subscribe_email" type="email" required class="form-control form-control-lg rounded-pill rounded-end" id="pb_subscribe_email" placeholder="<?php esc_attr_e( 'Your Email', 'purple-buzz' ); ?>">
							<button class="btn btn-secondary text-white btn-lg rounded-pill rounded-start px-lg-4" type="submit"><?php esc_html_e( 'Subscribe', 'purple-buzz' ); ?></button>
						</div>
						<p class="text-center light-300">
							<?php esc_html_e( 'Get occasional notes on the work we ship. No noise, unsubscribe any time.', 'purple-buzz' ); ?>
						</p>
					</form>
				</div>
			</div>
		</div>
	</section>
	<!-- End Contact -->

</main>

<?php
get_footer();
