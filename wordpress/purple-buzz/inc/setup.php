<?php
/**
 * Theme supports, menus and image sizes.
 *
 * @package Purple_Buzz
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

/**
 * Registers theme supports and navigation menus.
 */
function purple_buzz_setup() {
	load_theme_textdomain( 'purple-buzz', PURPLE_BUZZ_DIR . '/languages' );

	add_theme_support( 'automatic-feed-links' );
	add_theme_support( 'title-tag' );
	add_theme_support( 'post-thumbnails' );
	add_theme_support( 'responsive-embeds' );
	add_theme_support( 'align-wide' );
	add_theme_support( 'custom-logo', array(
		'height'      => 48,
		'width'       => 48,
		'flex-height' => true,
		'flex-width'  => true,
	) );
	add_theme_support( 'html5', array(
		'search-form',
		'comment-form',
		'comment-list',
		'gallery',
		'caption',
		'style',
		'script',
		'navigation-widgets',
	) );

	register_nav_menus( array(
		'primary' => __( 'Primary Menu', 'purple-buzz' ),
	) );

	add_image_size( 'purple-buzz-card', 800, 600, true );
	add_image_size( 'purple-buzz-portrait', 480, 480, true );
}
add_action( 'after_setup_theme', 'purple_buzz_setup' );

/**
 * Sets the content width of the theme, in pixels.
 */
function purple_buzz_content_width() {
	$GLOBALS['content_width'] = apply_filters( 'purple_buzz_content_width', 1140 );
}
add_action( 'after_setup_theme', 'purple_buzz_content_width', 0 );

/**
 * Adds a widget area for the footer if needed later on.
 */
function purple_buzz_widgets_init() {
	register_sidebar( array(
		'name'          => __( 'Footer Widgets', 'purple-buzz' ),
		'id'            => 'footer-widgets',
		'description'   => __( 'Optional widgets rendered above the footer columns.', 'purple-buzz' ),
		'before_widget' => '<div id="%1$s" class="widget %2$s">',
		'after_widget'  => '</div>',
		'before_title'  => '<h3 class="h4 pb-lg-3 text-light light-300">',
		'after_title'   => '</h3>',
	) );
}
add_action( 'widgets_init', 'purple_buzz_widgets_init' );
