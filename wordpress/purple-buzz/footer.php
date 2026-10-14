<?php
/**
 * Site footer.
 *
 * @package Purple_Buzz
 */

$pb_socials = array(
	'pb_facebook' => array( 'icon' => 'bxl-facebook-square', 'label' => __( 'Facebook', 'purple-buzz' ) ),
	'pb_linkedin' => array( 'icon' => 'bxl-linkedin-square', 'label' => __( 'LinkedIn', 'purple-buzz' ) ),
	'pb_whatsapp' => array( 'icon' => 'bxl-whatsapp-square', 'label' => __( 'WhatsApp', 'purple-buzz' ) ),
	'pb_flickr'   => array( 'icon' => 'bxl-flickr-square', 'label' => __( 'Flickr', 'purple-buzz' ) ),
	'pb_medium'   => array( 'icon' => 'bxl-medium-square', 'label' => __( 'Medium', 'purple-buzz' ) ),
);

$pb_work_terms = get_terms(
	array(
		'taxonomy'   => 'work_category',
		'hide_empty' => false,
	)
);
?>

<!-- Start Footer -->
<footer class="bg-secondary pt-4">
	<?php if ( is_active_sidebar( 'footer-widgets' ) ) : ?>
		<div class="container pb-3">
			<?php dynamic_sidebar( 'footer-widgets' ); ?>
		</div>
	<?php endif; ?>

	<div class="container">
		<div class="row py-4">

			<div class="col-lg-3 col-12 align-left">
				<a class="navbar-brand" href="<?php echo esc_url( home_url( '/' ) ); ?>" rel="home">
					<i class="bx bx-buildings bx-sm text-light"></i>
					<span class="text-light h5"><?php bloginfo( 'name' ); ?></span>
				</a>
				<p class="text-light my-lg-4 my-2">
					<?php echo wp_kses_post( purple_buzz_mod( 'pb_footer_blurb', 'Lorem ipsum dolor sit amet, consectetur adipisicing elit, sed do eiusmod tempor incididunt ut.' ) ); ?>
				</p>
				<ul class="list-inline footer-icons light-300">
					<?php foreach ( $pb_socials as $mod => $social ) : ?>
						<?php $url = purple_buzz_mod( $mod ); ?>
						<?php if ( $url ) : ?>
							<li class="list-inline-item m-0">
								<a class="text-light" target="_blank" rel="noopener noreferrer" href="<?php echo esc_url( $url ); ?>" aria-label="<?php echo esc_attr( $social['label'] ); ?>">
									<i class="bx <?php echo esc_attr( $social['icon'] ); ?> bx-md"></i>
								</a>
							</li>
						<?php endif; ?>
					<?php endforeach; ?>
				</ul>
			</div>

			<div class="col-lg-3 col-md-4 my-sm-0 mt-4">
				<h3 class="h4 pb-lg-3 text-light light-300"><?php esc_html_e( 'Our Company', 'purple-buzz' ); ?></h3>
				<?php
				wp_nav_menu(
					array(
						'theme_location' => 'primary',
						'container'      => false,
						'menu_class'     => 'list-unstyled text-light light-300',
						'depth'          => 1,
						'fallback_cb'    => 'purple_buzz_menu_fallback',
						'pb_context'     => 'footer',
						'link_before'    => "<i class='bx-fw bx bxs-chevron-right bx-xs'></i>",
					)
				);
				?>
			</div>

			<div class="col-lg-3 col-md-4 my-sm-0 mt-4">
				<h3 class="h4 pb-lg-3 text-light light-300"><?php esc_html_e( 'Our Works', 'purple-buzz' ); ?></h3>
				<ul class="list-unstyled text-light light-300">
					<?php if ( ! is_wp_error( $pb_work_terms ) && ! empty( $pb_work_terms ) ) : ?>
						<?php foreach ( $pb_work_terms as $pb_term ) : ?>
							<li class="pb-2">
								<i class="bx-fw bx bxs-chevron-right bx-xs"></i>
								<a class="text-decoration-none text-light py-1" href="<?php echo esc_url( get_term_link( $pb_term ) ); ?>">
									<?php echo esc_html( $pb_term->name ); ?>
								</a>
							</li>
						<?php endforeach; ?>
					<?php else : ?>
						<li class="pb-2">
							<i class="bx-fw bx bxs-chevron-right bx-xs"></i>
							<a class="text-decoration-none text-light py-1" href="<?php echo esc_url( get_post_type_archive_link( 'work' ) ); ?>">
								<?php esc_html_e( 'All Work', 'purple-buzz' ); ?>
							</a>
						</li>
					<?php endif; ?>
				</ul>
			</div>

			<div class="col-lg-3 col-md-4 my-sm-0 mt-4">
				<h3 class="h4 pb-lg-3 text-light light-300"><?php esc_html_e( 'For Client', 'purple-buzz' ); ?></h3>
				<ul class="list-unstyled text-light light-300">
					<?php $pb_phone = purple_buzz_mod( 'pb_phone', '010-020-0340' ); ?>
					<?php if ( $pb_phone ) : ?>
						<li class="pb-2">
							<i class="bx-fw bx bx-phone bx-xs"></i>
							<a class="text-decoration-none text-light py-1" href="tel:<?php echo esc_attr( preg_replace( '/[^0-9+]/', '', $pb_phone ) ); ?>"><?php echo esc_html( $pb_phone ); ?></a>
						</li>
					<?php endif; ?>
					<?php $pb_email = purple_buzz_mod( 'pb_email', 'info@company.com' ); ?>
					<?php if ( $pb_email ) : ?>
						<li class="pb-2">
							<i class="bx-fw bx bx-mail-send bx-xs"></i>
							<a class="text-decoration-none text-light py-1" href="mailto:<?php echo esc_attr( antispambot( $pb_email ) ); ?>"><?php echo esc_html( antispambot( $pb_email ) ); ?></a>
						</li>
					<?php endif; ?>
				</ul>
			</div>

		</div>
	</div>

	<div class="w-100 bg-primary py-3">
		<div class="container">
			<div class="row pt-2">
				<div class="col-lg-6 col-sm-12">
					<p class="text-lg-start text-center text-light light-300">
						<?php echo wp_kses_post( purple_buzz_mod( 'pb_copyright', '© Copyright 2021 Purple Buzz Company. All Rights Reserved.' ) ); ?>
					</p>
				</div>
				<div class="col-lg-6 col-sm-12">
					<p class="text-lg-end text-center text-light light-300">
						<?php
						printf(
							/* translators: %s: theme author link */
							wp_kses_post( __( 'Designed by %s', 'purple-buzz' ) ),
							'<a rel="sponsored" class="text-decoration-none text-light" href="https://templatemo.com/" target="_blank" rel="noopener noreferrer"><strong>TemplateMo</strong></a>'
						);
						?>
					</p>
				</div>
			</div>
		</div>
	</div>

</footer>
<!-- End Footer -->

<?php wp_footer(); ?>
</body>
</html>
