<?php
/**
 * Template Name: Contact
 *
 * @package Purple_Buzz
 */

get_header();

$pb_phone = purple_buzz_mod( 'pb_phone', '010-020-0340' );
$pb_email = purple_buzz_mod( 'pb_email', 'info@company.com' );

$pb_contacts = array(
	array(
		'icon'  => 'bx-news',
		'title' => __( 'Media Contact', 'purple-buzz' ),
		'name'  => 'Mr. John Doe',
	),
	array(
		'icon'  => 'bx-laptop',
		'title' => __( 'Technical Contact', 'purple-buzz' ),
		'name'  => 'Mr. John Stiles',
	),
	array(
		'icon'  => 'bx-money',
		'title' => __( 'Billing Contact', 'purple-buzz' ),
		'name'  => 'Mr. Richard Miles',
	),
);
?>

<main id="primary" class="site-main">

	<?php
	while ( have_posts() ) {
		the_post();
		?>

		<!-- Start Banner Hero -->
		<section class="bg-light">
			<div class="container py-4">
				<div class="row align-items-center justify-content-between">
					<div class="contact-header col-lg-4">
						<h1 class="h2 pb-3 text-primary"><?php the_title(); ?></h1>
						<h2 class="h4 regular-400"><?php echo wp_kses_post( get_the_excerpt() ? get_the_excerpt() : __( 'Elit, sed do eiusmod tempor', 'purple-buzz' ) ); ?></h2>
						<p class="light-300">
							<?php esc_html_e( 'Incididunt ut labore et dolore magna aliqua. Quis ipsum suspendisse ultrices gravida.', 'purple-buzz' ); ?>
						</p>
					</div>
					<div class="contact-img col-lg-5 align-items-end col-md-4">
						<img src="<?php echo esc_url( PURPLE_BUZZ_URI . '/assets/img/banner-img-01.svg' ); ?>" alt="" width="500" height="360" loading="lazy">
					</div>
				</div>
			</div>
		</section>
		<!-- End Banner Hero -->

		<!-- Start Contact -->
		<section class="container py-5">

			<h2 class="col-12 col-xl-8 h2 text-left text-primary pt-3"><?php esc_html_e( 'Create success campaign with us!', 'purple-buzz' ); ?></h2>
			<h3 class="col-12 col-xl-8 h4 text-left regular-400"><?php esc_html_e( 'Elit, sed do eiusmod tempor', 'purple-buzz' ); ?></h3>
			<p class="col-12 col-xl-8 text-left text-muted pb-5 light-300">
				<?php esc_html_e( 'Incididunt ut labore et dolore magna aliqua. Quis ipsum suspendisse ultrices gravida. Tell us what you are building and we will come back with a plan.', 'purple-buzz' ); ?>
			</p>

			<?php purple_buzz_contact_notice(); ?>

			<?php if ( trim( get_the_content() ) ) : ?>
				<div class="row pb-4">
					<div class="col-12"><?php the_content(); ?></div>
				</div>
			<?php endif; ?>

			<div class="row pb-4">
				<div class="col-lg-4">

					<?php foreach ( $pb_contacts as $pb_contact ) : ?>
						<div class="contact row mb-4">
							<div class="contact-icon col-lg-3 col-3">
								<div class="border py-3 mb-2 text-center border rounded text-secondary">
									<i class="display-6 bx <?php echo esc_attr( $pb_contact['icon'] ); ?>"></i>
								</div>
							</div>
							<ul class="contact-info list-unstyled col-lg-9 col-9 light-300">
								<li class="h5 mb-0"><?php echo esc_html( $pb_contact['title'] ); ?></li>
								<li class="text-muted"><?php echo esc_html( $pb_contact['name'] ); ?></li>
								<li class="text-muted">
									<a class="text-decoration-none text-muted" href="tel:<?php echo esc_attr( preg_replace( '/[^0-9+]/', '', $pb_phone ) ); ?>"><?php echo esc_html( $pb_phone ); ?></a>
								</li>
								<li class="text-muted">
									<a class="text-decoration-none text-muted" href="mailto:<?php echo esc_attr( antispambot( $pb_email ) ); ?>"><?php echo esc_html( antispambot( $pb_email ) ); ?></a>
								</li>
							</ul>
						</div>
					<?php endforeach; ?>

				</div>

				<!-- Start Contact Form -->
				<div class="col-lg-8">
					<form class="contact-form row" method="post" action="<?php echo esc_url( admin_url( 'admin-post.php' ) ); ?>" role="form">
						<input type="hidden" name="action" value="pb_contact">
						<?php wp_nonce_field( 'pb_contact', 'pb_contact_nonce' ); ?>
						<div class="col-lg-6 mb-4" aria-hidden="true">
							<label class="screen-reader-text" for="pb_website"><?php esc_html_e( 'Website', 'purple-buzz' ); ?></label>
							<input type="text" id="pb_website" name="pb_website" tabindex="-1" autocomplete="off">
						</div>

						<div class="col-lg-6 mb-4">
							<div class="form-floating">
								<input type="text" class="form-control form-control-lg light-300" id="floatingname" name="pb_name" placeholder="<?php esc_attr_e( 'Name', 'purple-buzz' ); ?>" required>
								<label for="floatingname" class="light-300"><?php esc_html_e( 'Name', 'purple-buzz' ); ?></label>
							</div>
						</div>

						<div class="col-lg-6 mb-4">
							<div class="form-floating">
								<input type="email" class="form-control form-control-lg light-300" id="floatingemail" name="pb_email_field" placeholder="<?php esc_attr_e( 'Email', 'purple-buzz' ); ?>" required>
								<label for="floatingemail" class="light-300"><?php esc_html_e( 'Email', 'purple-buzz' ); ?></label>
							</div>
						</div>

						<div class="col-lg-6 mb-4">
							<div class="form-floating">
								<input type="text" class="form-control form-control-lg light-300" id="floatingphone" name="pb_phone" placeholder="<?php esc_attr_e( 'Phone', 'purple-buzz' ); ?>">
								<label for="floatingphone" class="light-300"><?php esc_html_e( 'Phone', 'purple-buzz' ); ?></label>
							</div>
						</div>

						<div class="col-lg-6 mb-4">
							<div class="form-floating">
								<input type="text" class="form-control form-control-lg light-300" id="floatingcompany" name="pb_company" placeholder="<?php esc_attr_e( 'Company Name', 'purple-buzz' ); ?>">
								<label for="floatingcompany" class="light-300"><?php esc_html_e( 'Company Name', 'purple-buzz' ); ?></label>
							</div>
						</div>

						<div class="col-12">
							<div class="form-floating mb-4">
								<input type="text" class="form-control form-control-lg light-300" id="floatingsubject" name="pb_subject" placeholder="<?php esc_attr_e( 'Subject', 'purple-buzz' ); ?>">
								<label for="floatingsubject" class="light-300"><?php esc_html_e( 'Subject', 'purple-buzz' ); ?></label>
							</div>
						</div>

						<div class="col-12">
							<div class="form-floating mb-3">
								<label class="screen-reader-text" for="floatingtextarea"><?php esc_html_e( 'Message', 'purple-buzz' ); ?></label>
								<textarea class="form-control light-300" rows="8" placeholder="<?php esc_attr_e( 'Message', 'purple-buzz' ); ?>" id="floatingtextarea" name="pb_message" required></textarea>
								<label for="floatingtextarea" class="light-300"><?php esc_html_e( 'Message', 'purple-buzz' ); ?></label>
							</div>
						</div>

						<div class="col-md-12 col-12 m-auto text-end">
							<button type="submit" class="btn btn-secondary rounded-pill px-md-5 px-4 py-2 radius-0 text-light light-300"><?php esc_html_e( 'Send Message', 'purple-buzz' ); ?></button>
						</div>

					</form>
				</div>
				<!-- End Contact Form -->

			</div>
		</section>
		<!-- End Contact -->

		<?php
	}
	?>

</main>

<?php
get_footer();
