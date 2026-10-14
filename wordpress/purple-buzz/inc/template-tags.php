<?php
/**
 * Template helpers.
 *
 * @package Purple_Buzz
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

/**
 * Prints post meta (date, author, categories).
 */
function purple_buzz_posted_on() {
	$time_string = '<time class="entry-date published updated" datetime="%1$s">%2$s</time>';
	if ( get_the_time( 'U' ) !== get_the_modified_time( 'U' ) ) {
		$time_string = '<time class="entry-date published" datetime="%1$s">%2$s</time><time class="updated d-none" datetime="%3$s">%4$s</time>';
	}

	$time_string = sprintf(
		$time_string,
		esc_attr( get_the_date( DATE_W3C ) ),
		esc_html( get_the_date() ),
		esc_attr( get_the_modified_date( DATE_W3C ) ),
		esc_html( get_the_modified_date() )
	);

	printf(
		'<span class="posted-on text-muted light-300">%1$s <a class="text-decoration-none text-primary" href="%2$s" rel="bookmark">%3$s</a></span> <span class="byline text-muted light-300"> %4$s <a class="text-decoration-none text-primary" href="%5$s">%6$s</a></span>',
		esc_html__( 'Posted on', 'purple-buzz' ),
		esc_url( get_permalink() ),
		$time_string,
		esc_html__( 'by', 'purple-buzz' ),
		esc_url( get_author_posts_url( get_the_author_meta( 'ID' ) ) ),
		esc_html( get_the_author() )
	);
}

/**
 * Prints categories and comments link for the current post.
 */
function purple_buzz_entry_footer() {
	if ( 'post' === get_post_type() ) {
		/* translators: used between list items */
		$categories_list = get_the_category_list( esc_html__( ', ', 'purple-buzz' ) );
		if ( $categories_list ) {
			printf(
				'<span class="cat-links text-muted light-300">%1$s %2$s</span>',
				esc_html__( 'Posted in', 'purple-buzz' ),
				$categories_list // phpcs:ignore WordPress.Security.EscapeOutput.OutputNotEscaped -- built by core with escaping.
			);
		}
	}

	if ( ! is_single() && ! post_password_required() && ( comments_open() || get_comments_number() ) ) {
		echo '<span class="comments-link text-muted light-300">';
		comments_popup_link(
			sprintf(
				/* translators: %s: post title */
				wp_kses_post( __( 'Leave a Comment<span class="screen-reader-text"> on %s</span>', 'purple-buzz' ) ),
				get_the_title()
			)
		);
		echo '</span>';
	}

	edit_post_link(
		sprintf(
			/* translators: %s: post title */
			wp_kses_post( __( 'Edit <span class="screen-reader-text">%s</span>', 'purple-buzz' ) ),
			get_the_title()
		),
		'<span class="edit-link text-muted light-300 ms-2">',
		'</span>'
	);
}

/**
 * Returns the post thumbnail URL, falling back to a bundled theme image so
 * cards are never empty.
 *
 * @param int    $post_id Post ID.
 * @param string $size    Image size.
 * @return string Image URL.
 */
function purple_buzz_thumbnail_url( $post_id = 0, $size = 'purple-buzz-card' ) {
	$post_id = $post_id ? $post_id : get_the_ID();

	if ( has_post_thumbnail( $post_id ) ) {
		$url = get_the_post_thumbnail_url( $post_id, $size );
		if ( $url ) {
			return $url;
		}
	}

	$fallbacks = array(
		'assets/img/services-01.jpg',
		'assets/img/services-02.jpg',
		'assets/img/services-03.jpg',
		'assets/img/services-04.jpg',
		'assets/img/recent-work-01.jpg',
		'assets/img/recent-work-02.jpg',
		'assets/img/recent-work-03.jpg',
	);

	return PURPLE_BUZZ_URI . '/' . $fallbacks[ absint( $post_id ) % count( $fallbacks ) ];
}

/**
 * Prints the page/entry banner used by singular and archive templates.
 *
 * @param string      $subtitle Optional subtitle line.
 * @param string|null $title    Optional explicit banner title.
 */
function purple_buzz_page_banner( $subtitle = '', $title = null ) {
	if ( null === $title ) {
		if ( is_archive() ) {
			$title = get_the_archive_title();
		} elseif ( is_singular() ) {
			$title = get_the_title();
		} else {
			$title = get_bloginfo( 'name' );
		}
	}
	?>
	<div class="banner-wrapper bg-light w-100 py-5">
		<div class="banner-vertical-center-work container text-light d-flex justify-content-center align-items-center py-5 p-0">
			<div class="banner-content col-lg-8 col-12 m-lg-auto text-center">
				<h1 class="banner-heading h2 display-3 pb-5 semi-bold-600 typo-space-line-center">
					<?php echo wp_kses_post( $title ); ?>
				</h1>
				<?php if ( $subtitle ) : ?>
					<h3 class="h4 pb-2 regular-400"><?php echo wp_kses_post( $subtitle ); ?></h3>
				<?php endif; ?>
				<?php if ( is_archive() && get_the_archive_description() ) : ?>
					<div class="banner-body pb-2 light-300"><?php the_archive_description(); ?></div>
				<?php endif; ?>
			</div>
		</div>
	</div>
	<?php
}

/**
 * Returns the theme mod with a safe fallback.
 *
 * @param string $key     Mod key.
 * @param string $default Default value.
 * @return string
 */
function purple_buzz_mod( $key, $default = '' ) {
	return get_theme_mod( $key, $default );
}

/**
 * Returns the URL of the page using a given template file, or the home URL.
 *
 * @param string $template Template file relative to the theme root.
 * @return string
 */
function purple_buzz_page_url( $template ) {
	$pages = get_posts(
		array(
			'post_type'      => 'page',
			'meta_key'       => '_wp_page_template',
			'meta_value'     => $template,
			'posts_per_page' => 1,
			'fields'         => 'ids',
		)
	);

	return $pages ? (string) get_permalink( $pages[0] ) : home_url( '/' );
}

/**
 * Renders the posts pagination with Bootstrap friendly markup.
 */
function purple_buzz_pagination() {
	the_posts_pagination(
		array(
			'mid_size'  => 2,
			'prev_text' => __( 'Previous', 'purple-buzz' ),
			'next_text' => __( 'Next', 'purple-buzz' ),
		)
	);
}

/**
 * Comment list callback matching the template markup.
 *
 * @param WP_Comment $comment Comment object.
 * @param array      $args    Comment args.
 * @param int        $depth   Current depth.
 */
function purple_buzz_comment_callback( $comment, $args, $depth ) {
	?>
	<li id="comment-<?php comment_ID( $comment ); ?>" <?php comment_class( 'pb-comment', $comment ); ?>>
		<div class="d-flex pb-4">
			<div>
				<?php echo get_avatar( $comment, $args['avatar_size'] ?? 50, '', '', array( 'class' => 'rounded-circle' ) ); ?>
			</div>
			<div class="comment-body">
				<div class="comment-header d-flex justify-content-between ms-3">
					<div class="header text-start">
						<h5 class="h6"><?php comment_author_link( $comment ); ?></h5>
						<p class="text-muted light-300 mb-0">
							<a class="text-decoration-none text-muted" href="<?php echo esc_url( get_comment_link( $comment ) ); ?>">
								<?php echo esc_html( get_comment_date( '', $comment ) ); ?> <?php echo esc_html( get_comment_time( '', false, $comment ) ); ?>
							</a>
						</p>
					</div>
					<?php
					comment_reply_link(
						array_merge(
							$args,
							array(
								'depth'     => $depth,
								'max_depth' => $args['max_depth'] ?? 0,
								'before'    => '<a class="text-decoration-none text-secondary">',
								'after'     => '</a>',
							)
						)
					);
					?>
				</div>
				<div class="footer">
					<div class="card-body border ms-3 light-300">
						<?php comment_text( $comment ); ?>
						<?php edit_comment_link( __( 'Edit', 'purple-buzz' ), '<span class="edit-link small d-block pt-2">', '</span>' ); ?>
					</div>
				</div>
			</div>
		</div>
	<?php
}
