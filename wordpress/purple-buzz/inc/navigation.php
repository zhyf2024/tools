<?php
/**
 * Navigation helpers: menu classes matching the Bootstrap template markup
 * and a page-list fallback when no menu is assigned yet.
 *
 * @package Purple_Buzz
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

/**
 * Returns the rendering context of the menu currently being printed.
 *
 * @param mixed $args Menu args.
 * @return string
 */
function purple_buzz_menu_context( $args ) {
	if ( is_object( $args ) && isset( $args->pb_context ) ) {
		return $args->pb_context;
	}
	return 'header';
}

/**
 * Adds Bootstrap classes to menu items.
 *
 * @param array    $classes Classes.
 * @param WP_Post  $item    Menu item.
 * @param stdClass $args    Menu args.
 * @return array
 */
function purple_buzz_nav_menu_css_class( $classes, $item, $args ) {
	if ( 'footer' === purple_buzz_menu_context( $args ) ) {
		$classes[] = 'pb-2';
	} else {
		$classes[] = 'nav-item';
	}
	return $classes;
}
add_filter( 'nav_menu_css_class', 'purple_buzz_nav_menu_css_class', 10, 3 );

/**
 * Adds Bootstrap classes to menu links and the chevron icon in the footer.
 *
 * @param array    $atts Link attributes.
 * @param WP_Post  $item Menu item.
 * @param stdClass $args Menu args.
 * @return array
 */
function purple_buzz_nav_menu_link_attributes( $atts, $item, $args ) {
	$context = purple_buzz_menu_context( $args );
	$current = in_array( 'current-menu-item', (array) ( $item->classes ?? array() ), true );

	if ( 'footer' === $context ) {
		$atts['class'] = 'text-decoration-none text-light py-1';
	} else {
		$atts['class'] = 'nav-link btn-outline-primary rounded-pill px-3' . ( $current ? ' active' : '' );
	}
	return $atts;
}
add_filter( 'nav_menu_link_attributes', 'purple_buzz_nav_menu_link_attributes', 10, 3 );

/**
 * Fallback menu built from the page list, matching the theme markup.
 *
 * @param stdClass $args Menu args.
 */
function purple_buzz_menu_fallback( $args ) {
	$pages = get_pages( array( 'sort_column' => 'menu_order' ) );
	if ( ! $pages ) {
		return;
	}

	$context = purple_buzz_menu_context( $args );
	$front   = (int) get_option( 'page_on_front' );

	echo '<ul class="' . esc_attr( $args->menu_class ?? '' ) . '">';
	foreach ( $pages as $page ) {
		$current = is_page( $page->ID ) || ( $front && $front === (int) $page->ID && is_front_page() );
		$class   = 'footer' === $context ? 'text-decoration-none text-light py-1' : 'nav-link btn-outline-primary rounded-pill px-3' . ( $current ? ' active' : '' );
		$li      = 'footer' === $context ? 'pb-2' : 'nav-item' . ( $current ? ' current-menu-item' : '' );
		$icon    = 'footer' === $context ? "<i class='bx-fw bx bxs-chevron-right bx-xs'></i>" : '';
		?>
		<li class="<?php echo esc_attr( $li ); ?>">
			<a class="<?php echo esc_attr( $class ); ?>" href="<?php echo esc_url( get_permalink( $page ) ); ?>">
				<?php echo $icon . esc_html( $page->post_title ); // phpcs:ignore WordPress.Security.EscapeOutput.OutputNotEscaped -- static icon markup. ?>
			</a>
		</li>
		<?php
	}
	echo '</ul>';
}
