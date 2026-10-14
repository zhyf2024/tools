<?php
/**
 * Registers the custom Gutenberg blocks (block.json based, no build step).
 *
 * @package Purple_Buzz
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

/**
 * Registers every block directory shipped with the theme.
 */
function purple_buzz_register_blocks() {
	$blocks = array(
		'cta-banner',
		'pricing-card',
	);

	foreach ( $blocks as $block ) {
		$path = PURPLE_BUZZ_DIR . '/blocks/' . $block;
		if ( file_exists( $path . '/block.json' ) ) {
			register_block_type( $path );
		}
	}
}
add_action( 'init', 'purple_buzz_register_blocks' );
