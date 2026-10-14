<?php
/**
 * Classic meta boxes for the code-registered meta fields, so non-technical
 * editors can fill them without touching REST/API tooling.
 *
 * @package Purple_Buzz
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

/**
 * Returns the meta field definitions.
 *
 * @return array
 */
function purple_buzz_meta_fields() {
	return array(
		'pb_position' => array(
			'type'        => 'team',
			'label'       => __( 'Position / Role', 'purple-buzz' ),
			'placeholder' => __( 'e.g. Business Development', 'purple-buzz' ),
		),
		'pb_icon'     => array(
			'type'        => 'services',
			'label'       => __( 'Boxicons class', 'purple-buzz' ),
			'placeholder' => __( 'e.g. bx-gift', 'purple-buzz' ),
		),
		'pb_subtitle' => array(
			'type'        => array( 'work', 'services' ),
			'label'       => __( 'Banner subtitle', 'purple-buzz' ),
			'placeholder' => __( 'Secondary line under the title on the single view', 'purple-buzz' ),
		),
	);
}

/**
 * Registers the meta boxes.
 */
function purple_buzz_add_meta_boxes() {
	foreach ( purple_buzz_meta_fields() as $key => $field ) {
		$types = (array) $field['type'];
		foreach ( $types as $type ) {
			add_meta_box(
				'pb_' . $key,
				$field['label'],
				'purple_buzz_render_meta_box',
				$type,
				'side',
				'default',
				array( 'field' => $key )
			);
		}
	}
}
add_action( 'add_meta_boxes', 'purple_buzz_add_meta_boxes' );

/**
 * Renders a meta box.
 *
 * @param WP_Post $post     Current post.
 * @param array   $box      Meta box arguments.
 */
function purple_buzz_render_meta_box( $post, $box ) {
	$key   = $box['args']['field'];
	$field = purple_buzz_meta_fields()[ $key ];
	$value = get_post_meta( $post->ID, $key, true );
	wp_nonce_field( 'pb_meta_' . $key, 'pb_meta_nonce_' . $key );
	?>
	<label class="screen-reader-text" for="pb_<?php echo esc_attr( $key ); ?>">
		<?php echo esc_html( $field['label'] ); ?>
	</label>
	<input
		type="text"
		id="pb_<?php echo esc_attr( $key ); ?>"
		name="<?php echo esc_attr( $key ); ?>"
		value="<?php echo esc_attr( $value ); ?>"
		placeholder="<?php echo esc_attr( $field['placeholder'] ); ?>"
		class="widefat"
	>
	<?php
}

/**
 * Sanitizes and saves meta box values.
 *
 * @param int $post_id Post ID.
 */
function purple_buzz_save_meta( $post_id ) {
	if ( defined( 'DOING_AUTOSAVE' ) && DOING_AUTOSAVE ) {
		return;
	}
	if ( ! current_user_can( 'edit_post', $post_id ) ) {
		return;
	}

	foreach ( purple_buzz_meta_fields() as $key => $field ) {
		if ( ! isset( $_POST[ 'pb_meta_nonce_' . $key ], $_POST[ $key ] ) ) {
			continue;
		}
		if ( ! wp_verify_nonce( sanitize_key( $_POST[ 'pb_meta_nonce_' . $key ] ), 'pb_meta_' . $key ) ) {
			continue;
		}
		update_post_meta( $post_id, $key, sanitize_text_field( wp_unslash( $_POST[ $key ] ) ) );
	}
}
add_action( 'save_post', 'purple_buzz_save_meta' );
