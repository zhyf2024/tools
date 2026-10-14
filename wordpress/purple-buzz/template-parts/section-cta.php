<?php
/**
 * "View our work" call to action banner.
 *
 * @package Purple_Buzz
 */
?>
<!-- Start View Work -->
<section class="bg-secondary">
	<div class="container py-5">
		<div class="row d-flex justify-content-center text-center">
			<div class="col-lg-2 col-12 text-light align-items-center">
				<i class="display-1 bx bxs-box bx-lg"></i>
			</div>
			<div class="col-lg-7 col-12 text-light pt-2">
				<h3 class="h4 light-300"><?php esc_html_e( 'Great transformations successful', 'purple-buzz' ); ?></h3>
				<p class="light-300"><?php esc_html_e( 'Quis ipsum suspendisse ultrices gravida.', 'purple-buzz' ); ?></p>
			</div>
			<div class="col-lg-3 col-12 pt-4">
				<a href="<?php echo esc_url( get_post_type_archive_link( 'work' ) ); ?>" class="btn btn-primary rounded-pill btn-block shadow px-4 py-2">
					<?php esc_html_e( 'View Our Work', 'purple-buzz' ); ?>
				</a>
			</div>
		</div>
	</div>
</section>
<!-- End View Work -->
