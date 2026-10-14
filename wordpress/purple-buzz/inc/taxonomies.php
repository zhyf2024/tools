<?php
/**
 * Taxonomies — registered in code, never through the admin UI.
 *
 * @package Purple_Buzz
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

/**
 * Registers the Work and Service categories.
 */
function purple_buzz_register_taxonomies() {

	register_taxonomy(
		'work_category',
		array( 'work' ),
		array(
			'labels'            => array(
				'name'              => __( 'Work Categories', 'purple-buzz' ),
				'singular_name'     => __( 'Work Category', 'purple-buzz' ),
				'menu_name'         => __( 'Work Categories', 'purple-buzz' ),
				'all_items'         => __( 'All Work Categories', 'purple-buzz' ),
				'edit_item'         => __( 'Edit Work Category', 'purple-buzz' ),
				'view_item'         => __( 'View Work Category', 'purple-buzz' ),
				'update_item'       => __( 'Update Work Category', 'purple-buzz' ),
				'add_new_item'      => __( 'Add New Work Category', 'purple-buzz' ),
				'new_item_name'     => __( 'New Work Category Name', 'purple-buzz' ),
				'search_items'      => __( 'Search Work Categories', 'purple-buzz' ),
				'not_found'         => __( 'No work categories found.', 'purple-buzz' ),
			),
			'hierarchical'      => true,
			'public'            => true,
			'show_admin_column' => true,
			'show_in_rest'      => true,
			'rewrite'           => array( 'slug' => 'work-category' ),
		)
	);

	register_taxonomy(
		'service_category',
		array( 'services' ),
		array(
			'labels'            => array(
				'name'              => __( 'Service Categories', 'purple-buzz' ),
				'singular_name'     => __( 'Service Category', 'purple-buzz' ),
				'menu_name'         => __( 'Service Categories', 'purple-buzz' ),
				'all_items'         => __( 'All Service Categories', 'purple-buzz' ),
				'edit_item'         => __( 'Edit Service Category', 'purple-buzz' ),
				'view_item'         => __( 'View Service Category', 'purple-buzz' ),
				'update_item'       => __( 'Update Service Category', 'purple-buzz' ),
				'add_new_item'      => __( 'Add New Service Category', 'purple-buzz' ),
				'new_item_name'     => __( 'New Service Category Name', 'purple-buzz' ),
				'search_items'      => __( 'Search Service Categories', 'purple-buzz' ),
				'not_found'         => __( 'No service categories found.', 'purple-buzz' ),
			),
			'hierarchical'      => true,
			'public'            => true,
			'show_admin_column' => true,
			'show_in_rest'      => true,
			'rewrite'           => array( 'slug' => 'service-category' ),
		)
	);
}
add_action( 'init', 'purple_buzz_register_taxonomies' );

/**
 * Flushes rewrite rules once after the theme is activated, so the new
 * archive URLs resolve immediately.
 */
function purple_buzz_after_switch_theme() {
	purple_buzz_register_post_types();
	purple_buzz_register_taxonomies();
	flush_rewrite_rules();
}
add_action( 'after_switch_theme', 'purple_buzz_after_switch_theme' );
