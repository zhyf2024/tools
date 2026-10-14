<?php
/**
 * Customizer — contact details and social links used by the footer,
 * contact page and header.
 *
 * @package Purple_Buzz
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

/**
 * Registers Customizer settings.
 *
 * @param WP_Customize_Manager $wp_customize Customizer instance.
 */
function purple_buzz_customize_register( $wp_customize ) {

	$wp_customize->add_section(
		'purple_buzz_contact',
		array(
			'title'    => __( 'Contact & Social', 'purple-buzz' ),
			'priority' => 30,
		)
	);

	$settings = array(
		'pb_phone'           => array(
			'label'   => __( 'Phone', 'purple-buzz' ),
			'default' => '010-020-0340',
		),
		'pb_email'           => array(
			'label'   => __( 'Email', 'purple-buzz' ),
			'default' => 'info@company.com',
		),
		'pb_facebook'        => array(
			'label'   => __( 'Facebook URL', 'purple-buzz' ),
			'default' => 'http://facebook.com/',
		),
		'pb_linkedin'        => array(
			'label'   => __( 'LinkedIn URL', 'purple-buzz' ),
			'default' => 'https://www.linkedin.com/',
		),
		'pb_whatsapp'        => array(
			'label'   => __( 'WhatsApp URL', 'purple-buzz' ),
			'default' => 'https://www.whatsapp.com/',
		),
		'pb_flickr'          => array(
			'label'   => __( 'Flickr URL', 'purple-buzz' ),
			'default' => 'https://www.flickr.com/',
		),
		'pb_medium'          => array(
			'label'   => __( 'Medium URL', 'purple-buzz' ),
			'default' => 'https://www.medium.com/',
		),
		'pb_copyright'       => array(
			'label'   => __( 'Copyright line', 'purple-buzz' ),
			'default' => '© Copyright 2021 Purple Buzz Company. All Rights Reserved.',
		),
		'pb_footer_blurb'    => array(
			'label'   => __( 'Footer blurb', 'purple-buzz' ),
			'default' => 'Lorem ipsum dolor sit amet, consectetur adipisicing elit, sed do eiusmod tempor incididunt ut.',
		),
	);

	$url_keys = array( 'pb_facebook', 'pb_linkedin', 'pb_whatsapp', 'pb_flickr', 'pb_medium' );

	foreach ( $settings as $key => $args ) {
		if ( in_array( $key, $url_keys, true ) ) {
			$sanitize = 'esc_url_raw';
		} elseif ( 'pb_email' === $key ) {
			$sanitize = 'sanitize_email';
		} else {
			$sanitize = 'sanitize_text_field';
		}

		$wp_customize->add_setting(
			$key,
			array(
				'default'           => $args['default'],
				'sanitize_callback' => $sanitize,
				'transport'         => 'refresh',
			)
		);
		$wp_customize->add_control(
			$key,
			array(
				'label'   => $args['label'],
				'section' => 'purple_buzz_contact',
				'type'    => 'text',
			)
		);
	}
}
add_action( 'customize_register', 'purple_buzz_customize_register' );
