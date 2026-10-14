<?php
/**
 * Custom post types — registered in code, never through the admin UI.
 *
 * @package Purple_Buzz
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

/**
 * Registers the Work, Services and Team content types.
 */
function purple_buzz_register_post_types() {

	register_post_type(
		'work',
		array(
			'labels'       => array(
				'name'               => __( 'Work', 'purple-buzz' ),
				'singular_name'      => __( 'Work Item', 'purple-buzz' ),
				'menu_name'          => __( 'Work', 'purple-buzz' ),
				'add_new'            => __( 'Add New Work Item', 'purple-buzz' ),
				'add_new_item'       => __( 'Add New Work Item', 'purple-buzz' ),
				'edit_item'          => __( 'Edit Work Item', 'purple-buzz' ),
				'new_item'           => __( 'New Work Item', 'purple-buzz' ),
				'view_item'          => __( 'View Work Item', 'purple-buzz' ),
				'view_items'         => __( 'View Work Items', 'purple-buzz' ),
				'search_items'       => __( 'Search Work', 'purple-buzz' ),
				'not_found'          => __( 'No work items found.', 'purple-buzz' ),
				'not_found_in_trash' => __( 'No work items found in Trash.', 'purple-buzz' ),
				'all_items'          => __( 'All Work', 'purple-buzz' ),
				'featured_image'     => __( 'Work Cover Image', 'purple-buzz' ),
				'set_featured_image' => __( 'Set cover image', 'purple-buzz' ),
			),
			'public'       => true,
			'has_archive'  => 'work',
			'rewrite'      => array( 'slug' => 'work' ),
			'show_in_rest' => true,
			'menu_icon'    => 'dashicons-portfolio',
			'menu_position'=> 20,
			'supports'     => array( 'title', 'editor', 'thumbnail', 'excerpt', 'custom-fields', 'comments' ),
		)
	);

	register_post_type(
		'services',
		array(
			'labels'       => array(
				'name'               => __( 'Services', 'purple-buzz' ),
				'singular_name'      => __( 'Service', 'purple-buzz' ),
				'menu_name'          => __( 'Services', 'purple-buzz' ),
				'add_new'            => __( 'Add New Service', 'purple-buzz' ),
				'add_new_item'       => __( 'Add New Service', 'purple-buzz' ),
				'edit_item'          => __( 'Edit Service', 'purple-buzz' ),
				'new_item'           => __( 'New Service', 'purple-buzz' ),
				'view_item'          => __( 'View Service', 'purple-buzz' ),
				'search_items'       => __( 'Search Services', 'purple-buzz' ),
				'not_found'          => __( 'No services found.', 'purple-buzz' ),
				'not_found_in_trash' => __( 'No services found in Trash.', 'purple-buzz' ),
				'all_items'          => __( 'All Services', 'purple-buzz' ),
				'featured_image'     => __( 'Service Image', 'purple-buzz' ),
				'set_featured_image' => __( 'Set service image', 'purple-buzz' ),
			),
			'public'       => true,
			'has_archive'  => 'services',
			'rewrite'      => array( 'slug' => 'services' ),
			'show_in_rest' => true,
			'menu_icon'    => 'dashicons-heart',
			'menu_position'=> 21,
			'supports'     => array( 'title', 'editor', 'thumbnail', 'excerpt', 'custom-fields' ),
		)
	);

	register_post_type(
		'team',
		array(
			'labels'       => array(
				'name'               => __( 'Team', 'purple-buzz' ),
				'singular_name'      => __( 'Team Member', 'purple-buzz' ),
				'menu_name'          => __( 'Team', 'purple-buzz' ),
				'add_new'            => __( 'Add New Member', 'purple-buzz' ),
				'add_new_item'       => __( 'Add New Team Member', 'purple-buzz' ),
				'edit_item'          => __( 'Edit Team Member', 'purple-buzz' ),
				'new_item'           => __( 'New Team Member', 'purple-buzz' ),
				'view_item'          => __( 'View Team Member', 'purple-buzz' ),
				'search_items'       => __( 'Search Team', 'purple-buzz' ),
				'not_found'          => __( 'No team members found.', 'purple-buzz' ),
				'not_found_in_trash' => __( 'No team members found in Trash.', 'purple-buzz' ),
				'all_items'          => __( 'All Team Members', 'purple-buzz' ),
				'featured_image'     => __( 'Portrait Photo', 'purple-buzz' ),
				'set_featured_image' => __( 'Set portrait photo', 'purple-buzz' ),
			),
			'public'       => true,
			'has_archive'  => 'team',
			'rewrite'      => array( 'slug' => 'team' ),
			'show_in_rest' => true,
			'menu_icon'    => 'dashicons-groups',
			'menu_position'=> 22,
			'supports'     => array( 'title', 'editor', 'thumbnail', 'excerpt', 'custom-fields' ),
		)
	);
}
add_action( 'init', 'purple_buzz_register_post_types' );

/**
 * Registers code-defined meta fields editable through the block editor REST API.
 */
function purple_buzz_register_meta() {
	$fields = array(
		'pb_position' => array(
			'label'       => __( 'Position / Role', 'purple-buzz' ),
			'description' => __( 'Shown under the team member name.', 'purple-buzz' ),
			'types'       => array( 'team' ),
		),
		'pb_icon'     => array(
			'label'       => __( 'Boxicons class', 'purple-buzz' ),
			'description' => __( 'e.g. bx-gift — used on service cards.', 'purple-buzz' ),
			'types'       => array( 'services' ),
		),
		'pb_subtitle' => array(
			'label'       => __( 'Banner subtitle', 'purple-buzz' ),
			'description' => __( 'Secondary line shown under the title on single views.', 'purple-buzz' ),
			'types'       => array( 'work', 'services' ),
		),
	);

	foreach ( $fields as $key => $args ) {
		register_post_meta(
			$args['types'][0],
			$key,
			array(
				'single'       => true,
				'type'         => 'string',
				'description'  => $args['description'],
				'show_in_rest' => array(
					'type'       => 'string',
					'selector'   => '.pb-meta',
					'editorContext' => 'view',
				),
				'auth_callback' => function () {
					return current_user_can( 'edit_posts' );
				},
			)
		);
	}
}
add_action( 'init', 'purple_buzz_register_meta' );
