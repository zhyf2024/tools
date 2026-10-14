/**
 * CTA Banner — dynamic block editor script (no build step required).
 */
( function ( blocks, element, blockEditor, i18n ) {
	'use strict';

	var el = element.createElement;
	var __ = i18n.__;
	var registerBlockType = blocks.registerBlockType;
	var RichText = blockEditor.RichText;
	var useBlockProps = blockEditor.useBlockProps;

	function TextInput( props ) {
		return el( 'input', {
			type: 'text',
			className: 'form-control form-control-sm',
			value: props.value,
			placeholder: props.placeholder,
			'aria-label': props.label,
			onChange: function ( event ) {
				props.onChange( event.target.value );
			}
		} );
	}

	registerBlockType( 'purple-buzz/cta-banner', {
		apiVersion: 3,
		title: __( 'CTA Banner', 'purple-buzz' ),
		description: __( 'Full width call to action banner with icon, heading, text and button.', 'purple-buzz' ),
		category: 'design',
		icon: 'megaphone',
		keywords: [ 'cta', 'banner', 'button' ],
		textdomain: 'purple-buzz',
		supports: {
			html: false,
			align: [ 'wide', 'full' ],
			reusable: true
		},
		attributes: {
			heading: { type: 'string', default: 'Great transformations successful' },
			text: { type: 'string', default: 'Quis ipsum suspendisse ultrices gravida.' },
			icon: { type: 'string', default: 'bxs-box' },
			buttonLabel: { type: 'string', default: 'View Our Work' },
			buttonUrl: { type: 'string', default: '' }
		},

		edit: function ( props ) {
			var attributes = props.attributes;
			var setAttributes = props.setAttributes;
			var blockProps = useBlockProps( { className: 'pb-block-card' } );

			return el(
				'div',
				blockProps,
				el(
					'div',
					{ className: 'bg-secondary text-light rounded p-4 mb-3' },
					el(
						'p',
						{ className: 'mb-2 small text-white-50' },
						el( 'i', { className: 'bx ' + ( attributes.icon || 'bxs-box' ) + ' me-2' } ),
						__( 'Banner icon', 'purple-buzz' )
					),
					el( RichText, {
						tagName: 'h3',
						className: 'h4 light-300 text-white',
						value: attributes.heading,
						placeholder: __( 'Banner heading…', 'purple-buzz' ),
						onChange: function ( value ) {
							setAttributes( { heading: value } );
						},
						allowedFormats: [ 'core/bold', 'core/italic' ]
					} ),
					el( RichText, {
						tagName: 'p',
						className: 'light-300 text-white mb-0',
						value: attributes.text,
						placeholder: __( 'Banner supporting text…', 'purple-buzz' ),
						onChange: function ( value ) {
							setAttributes( { text: value } );
						}
					} )
				),
				el(
					'div',
					{ className: 'row g-2' },
					el(
						'div',
						{ className: 'col-md-4' },
						el( TextInput, {
							value: attributes.buttonLabel,
							label: __( 'Button label', 'purple-buzz' ),
							placeholder: __( 'Button label', 'purple-buzz' ),
							onChange: function ( value ) {
								setAttributes( { buttonLabel: value } );
							}
						} )
					),
					el(
						'div',
						{ className: 'col-md-5' },
						el( TextInput, {
							value: attributes.buttonUrl,
							label: __( 'Button URL', 'purple-buzz' ),
							placeholder: __( 'Button URL (https://…)', 'purple-buzz' ),
							onChange: function ( value ) {
								setAttributes( { buttonUrl: value } );
							}
						} )
					),
					el(
						'div',
						{ className: 'col-md-3' },
						el( TextInput, {
							value: attributes.icon,
							label: __( 'Boxicons class', 'purple-buzz' ),
							placeholder: __( 'Icon (bxs-box)', 'purple-buzz' ),
							onChange: function ( value ) {
								setAttributes( { icon: value } );
							}
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
