/**
 * Pricing Card — dynamic block editor script (no build step required).
 */
( function ( blocks, element, blockEditor, i18n ) {
	'use strict';

	var el = element.createElement;
	var __ = i18n.__;
	var registerBlockType = blocks.registerBlockType;
	var useBlockProps = blockEditor.useBlockProps;

	function field( props ) {
		return el( 'input', {
			type: 'text',
			className: 'form-control form-control-sm mb-2',
			value: props.value,
			placeholder: props.placeholder,
			'aria-label': props.label,
			onChange: function ( event ) {
				props.onChange( event.target.value );
			}
		} );
	}

	registerBlockType( 'purple-buzz/pricing-card', {
		apiVersion: 3,
		title: __( 'Pricing Card', 'purple-buzz' ),
		description: __( 'Pricing plan card with price, feature list and call to action button.', 'purple-buzz' ),
		category: 'design',
		icon: 'money-alt',
		keywords: [ 'pricing', 'plan', 'price' ],
		textdomain: 'purple-buzz',
		supports: {
			html: false,
			align: [ 'wide' ],
			reusable: true
		},
		attributes: {
			planName: { type: 'string', default: 'Standard Plan' },
			price: { type: 'string', default: '$120' },
			period: { type: 'string', default: '/Year' },
			features: { type: 'array', default: [ '25 to 99 Users', '10 TB space', 'Live Chat' ] },
			highlighted: { type: 'boolean', default: false },
			buttonLabel: { type: 'string', default: 'Get Now' },
			buttonUrl: { type: 'string', default: '' }
		},

		edit: function ( props ) {
			var attributes = props.attributes;
			var setAttributes = props.setAttributes;
			var blockProps = useBlockProps( { className: 'pb-block-card col-md-4' } );
			var featuresText = ( attributes.features || [] ).join( '\n' );

			return el(
				'div',
				blockProps,
				el(
					'div',
					{
						className: 'pricing-table card h-100 shadow-sm border-0 py-5' + ( attributes.highlighted ? ' bg-secondary' : '' )
					},
					el(
						'div',
						{ className: 'card-body text-center' },
						el( 'i', {
							className: 'pricing-table-icon display-3 bx bx-package ' + ( attributes.highlighted ? 'text-white' : 'text-secondary' )
						} ),
						el( 'div', { className: 'h5 semi-bold-600 pb-2' + ( attributes.highlighted ? ' text-white' : '' ) },
							__( 'Pricing card', 'purple-buzz' )
						),
						el( field, {
							value: attributes.planName,
							label: __( 'Plan name', 'purple-buzz' ),
							placeholder: __( 'Plan name', 'purple-buzz' ),
							onChange: function ( value ) { setAttributes( { planName: value } ); }
						} ),
						el(
							'div',
							{ className: 'input-group mb-2' },
							el( field, {
								value: attributes.price,
								label: __( 'Price', 'purple-buzz' ),
								placeholder: __( 'Price ($120)', 'purple-buzz' ),
								onChange: function ( value ) { setAttributes( { price: value } ); }
							} ),
							el( field, {
								value: attributes.period,
								label: __( 'Period', 'purple-buzz' ),
								placeholder: __( 'Period (/Year)', 'purple-buzz' ),
								onChange: function ( value ) { setAttributes( { period: value } ); }
							} )
						),
						el( 'label', { className: 'd-block small text-start pb-1' + ( attributes.highlighted ? ' text-white' : '') },
							__( 'Features (one per line)', 'purple-buzz' )
						),
						el( 'textarea', {
							className: 'form-control form-control-sm mb-2',
							rows: 5,
							value: featuresText,
							'aria-label': __( 'Features', 'purple-buzz' ),
							onChange: function ( event ) {
								setAttributes( { features: event.target.value.split( /\r?\n/ ) } );
							}
						} ),
						el(
							'div',
							{ className: 'form-check text-start mb-2' },
							el( 'input', {
								id: 'pb-pricing-highlight-' + props.clientId,
								type: 'checkbox',
								className: 'form-check-input',
								checked: !! attributes.highlighted,
								onChange: function ( event ) {
									setAttributes( { highlighted: event.target.checked } );
								}
							} ),
							el( 'label', {
								htmlFor: 'pb-pricing-highlight-' + props.clientId,
								className: 'form-check-label small' + ( attributes.highlighted ? ' text-white' : '' )
							}, __( 'Highlighted (dark) card', 'purple-buzz' ) )
						),
						el( field, {
							value: attributes.buttonLabel,
							label: __( 'Button label', 'purple-buzz' ),
							placeholder: __( 'Button label', 'purple-buzz' ),
							onChange: function ( value ) { setAttributes( { buttonLabel: value } ); }
						} ),
						el( field, {
							value: attributes.buttonUrl,
							label: __( 'Button URL', 'purple-buzz' ),
							placeholder: __( 'Button URL (https://…)', 'purple-buzz' ),
							onChange: function ( value ) { setAttributes( { buttonUrl: value } ); }
						} )
					)
				)
			);
		},

		save: function () {
			return null;
		}
	} );
} )( window.wp.blocks, window.wp.element, window.wp.blockEditor, window.wp.i18n );
