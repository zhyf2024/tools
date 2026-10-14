<?php
/**
 * Comments template.
 *
 * @package Purple_Buzz
 */

if ( post_password_required() ) {
	return;
}
?>

<div id="comments" class="comments-area pb-4">

	<?php if ( have_comments() ) : ?>
		<div class="worksingle-comment-heading col-12 pb-3">
			<h3 class="h5">
				<?php
				$pb_count = get_comments_number();
				printf(
					/* translators: %s: comment count */
					esc_html( _n( '%s Comment', '%s Comments', $pb_count, 'purple-buzz' ) ),
					esc_html( number_format_i18n( $pb_count ) )
				);
				?>
			</h3>
		</div>

		<ul class="comment-list list-unstyled pb-4">
			<?php
			wp_list_comments(
				array(
					'style'       => 'ul',
					'avatar_size' => 50,
					'callback'    => 'purple_buzz_comment_callback',
				)
			);
			?>
		</ul>

		<?php
		the_comments_pagination(
			array(
				'prev_text' => __( 'Older Comments', 'purple-buzz' ),
				'next_text' => __( 'Newer Comments', 'purple-buzz' ),
			)
		);
		?>

	<?php endif; ?>

	<?php if ( ! comments_open() && get_comments_number() && post_type_supports( get_post_type(), 'comments' ) ) : ?>
		<p class="no-comments light-300 text-muted"><?php esc_html_e( 'Comments are closed.', 'purple-buzz' ); ?></p>
	<?php endif; ?>

	<?php
	comment_form(
		array(
			'title_reply'        => __( 'Leave Comment', 'purple-buzz' ),
			'class_submit'       => 'btn btn-secondary text-white px-md-4 px-2 py-md-3 py-1 radius-0 light-300',
			'class_field'        => 'form-group pb-3',
			'label_submit'       => __( 'Send Message', 'purple-buzz' ),
			'comment_notes_before' => '<p class="pb-3 light-300 text-muted">' . __( 'Your email address will not be published.', 'purple-buzz' ) . '</p>',
		)
	);
	?>

</div>
