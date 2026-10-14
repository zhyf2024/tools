<?php
/**
 * Purple Buzz theme bootstrap.
 *
 * @package Purple_Buzz
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

define( 'PURPLE_BUZZ_VERSION', '1.0.0' );
define( 'PURPLE_BUZZ_DIR', get_template_directory() );
define( 'PURPLE_BUZZ_URI', get_template_directory_uri() );

require PURPLE_BUZZ_DIR . '/inc/setup.php';
require PURPLE_BUZZ_DIR . '/inc/navigation.php';
require PURPLE_BUZZ_DIR . '/inc/enqueue.php';
require PURPLE_BUZZ_DIR . '/inc/custom-post-types.php';
require PURPLE_BUZZ_DIR . '/inc/taxonomies.php';
require PURPLE_BUZZ_DIR . '/inc/meta-boxes.php';
require PURPLE_BUZZ_DIR . '/inc/template-tags.php';
require PURPLE_BUZZ_DIR . '/inc/customizer.php';
require PURPLE_BUZZ_DIR . '/inc/contact-form.php';
require PURPLE_BUZZ_DIR . '/inc/blocks.php';
