<?php
/**
 * Scripts and styles.
 *
 * @package Purple_Buzz
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

/**
 * Whether the current view uses the isotope filter grid.
 *
 * @return bool
 */
function purple_buzz_uses_isotope() {
	return is_front_page()
		|| is_post_type_archive( array( 'work', 'services' ) )
		|| is_tax( array( 'work_category', 'service_category' ) );
}

/**
 * Whether the current view uses the fsLightbox gallery.
 *
 * @return bool
 */
function purple_buzz_uses_lightbox() {
	return is_singular( 'work' ) || is_post_type_archive( 'work' ) || is_tax( 'work_category' );
}

/**
 * Enqueues front-end styles and scripts.
 */
function purple_buzz_enqueue_assets() {
	// Styles.
	wp_enqueue_style(
		'purple-buzz-bootstrap',
		PURPLE_BUZZ_URI . '/assets/css/bootstrap.min.css',
		array(),
		'5.3.3'
	);
	wp_enqueue_style(
		'purple-buzz-boxicons',
		PURPLE_BUZZ_URI . '/assets/css/boxicon.min.css',
		array(),
		'2.1.4'
	);
	wp_enqueue_style(
		'purple-buzz-fonts',
		'https://fonts.googleapis.com/css2?family=Open+Sans:wght@300;400;600&display=swap',
		array(),
		null
	);
	wp_enqueue_style(
		'purple-buzz-template',
		PURPLE_BUZZ_URI . '/assets/css/templatemo.css',
		array( 'purple-buzz-bootstrap' ),
		PURPLE_BUZZ_VERSION
	);
	wp_enqueue_style(
		'purple-buzz-custom',
		PURPLE_BUZZ_URI . '/assets/css/custom.css',
		array( 'purple-buzz-template' ),
		PURPLE_BUZZ_VERSION
	);
	wp_enqueue_style(
		'purple-buzz-theme',
		get_theme_file_uri( '/assets/css/theme.css' ),
		array( 'purple-buzz-custom' ),
		PURPLE_BUZZ_VERSION
	);

	// Bootstrap collapse needs its bundle; deferred as it is not render blocking critical.
	wp_enqueue_script(
		'purple-buzz-bootstrap',
		PURPLE_BUZZ_URI . '/assets/js/bootstrap.bundle.min.js',
		array(),
		'5.3.3',
		array( 'strategy' => 'defer' )
	);

	wp_enqueue_script( 'jquery' );

	// Conditional libraries are registered before theme.js so deferred
	// execution order guarantees they are available at DOM ready.
	if ( purple_buzz_uses_isotope() ) {
		wp_enqueue_script(
			'purple-buzz-isotope',
			PURPLE_BUZZ_URI . '/assets/js/isotope.pkgd.js',
			array( 'jquery' ),
			'3.0.6',
			array( 'strategy' => 'defer' )
		);
	}

	if ( purple_buzz_uses_lightbox() ) {
		wp_enqueue_script(
			'purple-buzz-lightbox',
			PURPLE_BUZZ_URI . '/assets/js/fslightbox.js',
			array(),
			PURPLE_BUZZ_VERSION,
			array( 'strategy' => 'defer' )
		);
	}

	wp_enqueue_script(
		'purple-buzz-theme',
		get_theme_file_uri( '/assets/js/theme.js' ),
		array( 'jquery' ),
		PURPLE_BUZZ_VERSION,
		array( 'strategy' => 'defer' )
	);
}
add_action( 'wp_enqueue_scripts', 'purple_buzz_enqueue_assets' );

/**
 * Adds the body class used by the sticky/pill navigation styles.
 *
 * @param array $classes Body classes.
 * @return array
 */
function purple_buzz_body_classes( $classes ) {
	if ( ! is_active_sidebar( 'footer-widgets' ) ) {
		$classes[] = 'no-footer-widgets';
	}
	return $classes;
}
add_filter( 'body_class', 'purple_buzz_body_classes' );
