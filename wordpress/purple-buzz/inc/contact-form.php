<?php
/**
 * Contact form processing for the Contact page template.
 *
 * The form posts to admin-post.php with a nonce; submissions are rate
 * limited per IP and delivered with wp_mail(). No secrets are stored.
 *
 * @package Purple_Buzz
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

/**
 * Handles front-end contact form submissions.
 */
function purple_buzz_handle_contact() {
	$redirect = remove_query_arg( array( 'pb_contact' ), wp_get_referer() );
	$redirect = $redirect ? $redirect : home_url( '/' );

	if ( ! isset( $_POST['pb_contact_nonce'] )
		|| ! wp_verify_nonce( sanitize_key( $_POST['pb_contact_nonce'] ), 'pb_contact' )
	) {
		wp_safe_redirect( add_query_arg( 'pb_contact', 'error', $redirect ) );
		exit;
	}

	// Basic rate limit: one submission per IP per minute.
	$ip   = isset( $_SERVER['REMOTE_ADDR'] ) ? sanitize_text_field( wp_unslash( $_SERVER['REMOTE_ADDR'] ) ) : '';
	$lock = 'pb_contact_' . md5( $ip );
	if ( get_transient( $lock ) ) {
		wp_safe_redirect( add_query_arg( 'pb_contact', 'limit', $redirect ) );
		exit;
	}

	// Honeypot: hidden field humans never fill in.
	if ( ! empty( $_POST['pb_website'] ) ) {
		wp_safe_redirect( add_query_arg( 'pb_contact', 'error', $redirect ) );
		exit;
	}

	$name    = isset( $_POST['pb_name'] ) ? sanitize_text_field( wp_unslash( $_POST['pb_name'] ) ) : '';
	$email   = isset( $_POST['pb_email_field'] ) ? sanitize_email( wp_unslash( $_POST['pb_email_field'] ) ) : '';
	$phone   = isset( $_POST['pb_phone'] ) ? sanitize_text_field( wp_unslash( $_POST['pb_phone'] ) ) : '';
	$company = isset( $_POST['pb_company'] ) ? sanitize_text_field( wp_unslash( $_POST['pb_company'] ) ) : '';
	$subject = isset( $_POST['pb_subject'] ) ? sanitize_text_field( wp_unslash( $_POST['pb_subject'] ) ) : '';
	$message = isset( $_POST['pb_message'] ) ? sanitize_textarea_field( wp_unslash( $_POST['pb_message'] ) ) : '';

	if ( empty( $name ) || empty( $message ) || ! is_email( $email ) ) {
		wp_safe_redirect( add_query_arg( 'pb_contact', 'error', $redirect ) );
		exit;
	}

	$body = sprintf(
		"Name: %s\nEmail: %s\nPhone: %s\nCompany: %s\n\n%s",
		$name,
		$email,
		$phone,
		$company,
		$message
	);

	$sent = wp_mail(
		get_option( 'admin_email' ),
		sprintf( '[%s] %s', get_bloginfo( 'name' ), $subject ? $subject : __( 'New contact message', 'purple-buzz' ) ),
		$body,
		array( 'Reply-To: ' . $name . ' <' . $email . '>' )
	);

	set_transient( $lock, 1, MINUTE_IN_SECONDS );

	wp_safe_redirect( add_query_arg( 'pb_contact', $sent ? 'sent' : 'error', $redirect ) );
	exit;
}
add_action( 'admin_post_pb_contact', 'purple_buzz_handle_contact' );
add_action( 'admin_post_nopriv_pb_contact', 'purple_buzz_handle_contact' );

/**
 * Handles newsletter-style subscribe submissions from the About page.
 */
function purple_buzz_handle_subscribe() {
	$redirect = remove_query_arg( array( 'pb_contact' ), wp_get_referer() );
	$redirect = $redirect ? $redirect : home_url( '/' );

	if ( ! isset( $_POST['pb_subscribe_nonce'] )
		|| ! wp_verify_nonce( sanitize_key( $_POST['pb_subscribe_nonce'] ), 'pb_subscribe' )
	) {
		wp_safe_redirect( add_query_arg( 'pb_contact', 'error', $redirect ) );
		exit;
	}

	$email = isset( $_POST['pb_subscribe_email'] ) ? sanitize_email( wp_unslash( $_POST['pb_subscribe_email'] ) ) : '';
	if ( ! is_email( $email ) ) {
		wp_safe_redirect( add_query_arg( 'pb_contact', 'error', $redirect ) );
		exit;
	}

	$sent = wp_mail(
		get_option( 'admin_email' ),
		sprintf( '[%s] %s', get_bloginfo( 'name' ), __( 'New subscriber', 'purple-buzz' ) ),
		sprintf( __( 'New subscriber: %s', 'purple-buzz' ), $email )
	);

	wp_safe_redirect( add_query_arg( 'pb_contact', $sent ? 'sent' : 'error', $redirect ) );
	exit;
}
add_action( 'admin_post_pb_subscribe', 'purple_buzz_handle_subscribe' );
add_action( 'admin_post_nopriv_pb_subscribe', 'purple_buzz_handle_subscribe' );

/**
 * Prints the status notice returned by the handler.
 */
function purple_buzz_contact_notice() {
	if ( ! isset( $_GET['pb_contact'] ) ) { // phpcs:ignore WordPress.Security.NonceVerification.Recommended -- display only.
		return;
	}

	$status = sanitize_key( $_GET['pb_contact'] ); // phpcs:ignore WordPress.Security.NonceVerification.Recommended -- display only.

	$messages = array(
		'sent'  => array( 'success', __( 'Thanks! Your message has been sent.', 'purple-buzz' ) ),
		'error' => array( 'danger', __( 'Something went wrong. Please check the required fields and try again.', 'purple-buzz' ) ),
		'limit' => array( 'warning', __( 'Please wait a moment before sending another message.', 'purple-buzz' ) ),
	);

	if ( ! isset( $messages[ $status ] ) ) {
		return;
	}
	?>
	<div class="alert alert-<?php echo esc_attr( $messages[ $status ][0] ); ?>" role="alert">
		<?php echo esc_html( $messages[ $status ][1] ); ?>
	</div>
	<?php
}
