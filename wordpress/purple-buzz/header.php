<?php
/**
 * Site header.
 *
 * @package Purple_Buzz
 */
?>
<!DOCTYPE html>
<html <?php language_attributes(); ?>>
<head>
	<meta charset="<?php bloginfo( 'charset' ); ?>">
	<meta name="viewport" content="width=device-width, initial-scale=1">
	<link rel="profile" href="https://gmpg.org/xfn/11">
	<?php wp_head(); ?>
</head>

<body <?php body_class(); ?>>
<?php wp_body_open(); ?>

<!-- Header -->
<nav id="main_nav" class="navbar navbar-expand-lg navbar-light bg-white shadow">
	<div class="container d-flex justify-content-between align-items-center">
		<a class="navbar-brand h1" href="<?php echo esc_url( home_url( '/' ) ); ?>" rel="home">
			<?php if ( has_custom_logo() ) : ?>
				<?php the_custom_logo(); ?>
			<?php else : ?>
				<i class="bx bx-buildings bx-sm text-dark"></i>
				<span class="text-dark h4"><?php bloginfo( 'name' ); ?></span>
			<?php endif; ?>
		</a>
		<button class="navbar-toggler border-0" type="button" data-bs-toggle="collapse" data-bs-target="#navbar-toggler-success" aria-controls="navbarSupportedContent" aria-expanded="false" aria-label="<?php esc_attr_e( 'Toggle navigation', 'purple-buzz' ); ?>">
			<span class="navbar-toggler-icon"></span>
		</button>

		<div class="align-self-center collapse navbar-collapse flex-fill d-lg-flex justify-content-lg-between" id="navbar-toggler-success">
			<div class="flex-fill mx-xl-5 mb-2">
				<?php
				wp_nav_menu(
					array(
						'theme_location' => 'primary',
						'container'      => false,
						'menu_class'     => 'nav navbar-nav d-flex justify-content-between mx-xl-5 text-center text-dark',
						'depth'          => 2,
						'fallback_cb'    => 'purple_buzz_menu_fallback',
						'pb_context'     => 'header',
					)
				);
				?>
			</div>
			<div class="navbar align-self-center d-flex">


<?php

$languages = pll_the_languages( array( 'raw' => 1 ) );

if ( ! empty( $languages ) ) : 
    $current_lang = array_filter( $languages, function( $lang ) {
        return ! empty( $lang['current_lang'] );
    });
    $current_lang = reset( $current_lang );
?>

    <div class="dropdown id="polylang-bootstrap-switcher"">

        <button class="btn btn-outline-secondary dropdown-toggle d-inline-flex align-items-center" 
                type="button" 
                id="langDropdown" 
                data-bs-toggle="dropdown" 
                aria-expanded="false">
            <?php if ( ! empty( $current_lang['flag'] ) ) : ?>
                <img src="<?php echo esc_url( $current_lang['flag'] ); ?>" alt="<?php echo esc_attr( $current_lang['name'] ); ?>" class="me-2" style="width: 20px; height: auto; border-radius: 2px;">
            <?php endif; ?>
            <span><?php //echo esc_html( $current_lang['name'] ); ?></span>
        </button>

        <ul class="dropdown-menu shadow-sm" aria-labelledby="langDropdown">
            <?php foreach ( $languages as $lang ) : 
                // 如果你想在下拉列表中隐藏当前语言，可以解开下面这行的注释：
                // if ( $lang['current_lang'] ) continue; 
                $active_class = $lang['current_lang'] ? 'active' : '';
            ?>
                <li>
                    <a class="dropdown-item d-flex align-items-center <?php echo $active_class; ?>" href="<?php echo esc_url( $lang['url'] ); ?>">
                        <?php if ( ! empty( $lang['flag'] ) ) : ?>
                            <img src="<?php echo esc_url( $lang['flag'] ); ?>" alt="<?php echo esc_attr( $lang['name'] ); ?>" class="me-2" style="width: 20px; height: auto; border-radius: 2px;">
                        <?php endif; ?>
                        <span><?php echo esc_html( $lang['name'] ); ?></span>
                    </a>
                </li>
            <?php endforeach; ?>
        </ul>
    </div>
<?php endif; ?>
 
				<a class="nav-link" href="<?php echo esc_url( home_url( '/feed/' ) ); ?>" aria-label="<?php esc_attr_e( 'News feed', 'purple-buzz' ); ?>"><i class="bx bx-bell bx-sm bx-tada-hover text-primary"></i></a>
				<a class="nav-link" href="<?php echo esc_url( admin_url( 'customize.php' ) ); ?>" aria-label="<?php esc_attr_e( 'Site settings', 'purple-buzz' ); ?>"><i class="bx bx-cog bx-sm text-primary"></i></a>
				<a class="nav-link" href="<?php echo esc_url( admin_url() ); ?>" aria-label="<?php esc_attr_e( 'Admin', 'purple-buzz' ); ?>"><i class="bx bx-user-circle bx-sm text-primary"></i></a>
			</div>
		</div>
	</div>
</nav>
<!-- Close Header -->
