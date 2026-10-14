<?php
/**
 * Work media gallery: featured image plus a thumbnail carousel built from
 * the images attached to the work item.
 *
 * @package Purple_Buzz
 */

$pb_attachments = get_posts(
	array(
		'post_type'      => 'attachment',
		'post_parent'    => get_the_ID(),
		'post_mime_type' => 'image',
		'orderby'        => 'menu_order',
		'order'          => 'ASC',
		'posts_per_page' => 12,
		'no_found_rows'  => true,
	)
);

$pb_main = has_post_thumbnail() ? get_the_post_thumbnail_url( get_the_ID(), 'large' ) : '';

if ( ! $pb_attachments ) {
	if ( $pb_main ) {
		?>
		<div class="row justify-content-center pb-4">
			<div class="col-lg-8">
				<img class="img-fluid border rounded" src="<?php echo esc_url( $pb_main ); ?>" alt="<?php the_title_attribute(); ?>">
			</div>
		</div>
		<?php
	}
	return;
}

if ( ! $pb_main ) {
	$pb_main = wp_get_attachment_image_url( $pb_attachments[0]->ID, 'large' );
}

$pb_thumb_urls = array();
foreach ( $pb_attachments as $pb_attachment ) {
	$pb_thumb_urls[] = array(
		'thumb' => wp_get_attachment_image_url( $pb_attachment->ID, 'thumbnail' ),
		'full'  => wp_get_attachment_image_url( $pb_attachment->ID, 'full' ),
	);
}

$pb_chunks = array_chunk( $pb_thumb_urls, 5 );
$pb_uid    = 'pb_work_gallery_' . get_the_ID();
?>

<div class="row justify-content-center pb-4">
	<div class="col-lg-8">
		<div id="templatemo-slide-link-target" class="card mb-3">
			<a data-fslightbox="<?php echo esc_attr( $pb_uid ); ?>" href="<?php echo esc_url( $pb_main ); ?>">
				<img class="img-fluid border rounded" src="<?php echo esc_url( $pb_main ); ?>" alt="<?php the_title_attribute(); ?>">
			</a>
		</div>

		<?php if ( count( $pb_thumb_urls ) > 1 ) : ?>
			<div class="worksingle-slide-footer row">
				<div class="col-1 align-self-center">
					<a href="#<?php echo esc_attr( $pb_uid ); ?>" role="button" data-bs-slide="prev">
						<i class="bx bxs-chevron-left bx-sm text-dark"></i>
					</a>
				</div>

				<div id="<?php echo esc_attr( $pb_uid ); ?>" class="col-10 carousel slide" data-bs-ride="carousel">
					<div class="carousel-inner" role="listbox">
						<?php foreach ( $pb_chunks as $pb_index => $pb_chunk ) : ?>
							<div class="carousel-item <?php echo 0 === $pb_index ? 'active' : ''; ?>">
								<div class="row">
									<?php foreach ( $pb_chunk as $pb_image ) : ?>
										<div class="col">
											<a class="templatemo-slide-link" data-fslightbox="<?php echo esc_attr( $pb_uid ); ?>" href="<?php echo esc_url( $pb_image['full'] ); ?>">
												<img class="img-fluid border rounded" src="<?php echo esc_url( $pb_image['thumb'] ); ?>" alt="<?php the_title_attribute(); ?>" loading="lazy">
											</a>
										</div>
									<?php endforeach; ?>
								</div>
							</div>
						<?php endforeach; ?>
					</div>
				</div>

				<div class="col-1 align-self-center text-end">
					<a href="#<?php echo esc_attr( $pb_uid ); ?>" role="button" data-bs-slide="next">
						<i class="bx bxs-chevron-right bx-sm text-dark"></i>
					</a>
				</div>
			</div>
		<?php endif; ?>
	</div>
</div>
