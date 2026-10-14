/**
 * Purple Buzz theme behaviour: isotope filtering for the work/services grids.
 */
( function ( $ ) {
	'use strict';

	function pbInitIsotope() {
		var $grid = $( '.projects' );

		if ( ! $grid.length || typeof $.fn.isotope !== 'function' ) {
			return;
		}

		$grid.isotope( {
			itemSelector: '.project',
			layoutMode: 'fitRows',
			percentPosition: true
		} );

		$( document ).on( 'click', '.filter-btn', function ( event ) {
			event.preventDefault();

			var filter = $( this ).data( 'filter' ) || '.project';

			$grid.isotope( { filter: filter } );

			$( '.filter-btn' ).removeClass( 'active shadow' );
			$( this ).addClass( 'active shadow' );
		} );

		// Re-layout once images finish loading so columns settle correctly.
		$grid.imagesLoaded ? $grid.imagesLoaded( function () { $grid.isotope( 'layout' ); } ) : null;
	}

	$( document ).ready( pbInitIsotope );
} )( jQuery );
