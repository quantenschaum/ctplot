/*
pyplot - python based data plotting tools
created for DESY Zeuthen
Copyright (C) 2012  Adam Lucke  

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>. 

$Id$
 */

/** ajax default settings */
$.ajaxSetup({
	url : 'webplot.py',
	dataType : 'json'
});

var speed='fast';

/** add .startsWith() function to string */
if (typeof String.prototype.startsWith != 'function') {
	String.prototype.startsWith = function(str) {
		return this.indexOf(str) == 0;
	};
}

/** does browser support svg? */
function supportsSvg() {
	return document.implementation.hasFeature(
			"http://www.w3.org/TR/SVG11/feature#Shape", "1.0")
}

var tables_and_vars = null;

/** get available HDF5 from server */
function sourcesBox() {
	var ddbox;
	$.ajax({
		data : {
			a : 'list'
		},
		async : false,
		success : function(data) {
			f = '';
			ddbox = $('<select>').attr('name', 's*');
			$('<option>').text('').val('').appendTo(ddbox);
			tables_and_vars = data;
			$.each(data, function(k, v) { // radiobutton for each
				coi = k.indexOf(':');
				file = k.substr(0, coi);
				tab = k.substr(coi + 1, k.length);
				opt = $('<option>').text(
						k.replace(/.*\/(.*)\.h5:(.*)/, '$1: ' + v[0])).val(k);
				if (opt.text().startsWith('x'))
					opt.addClass('expert')
				opt.appendTo(ddbox);
			});
		},
		error : function(xhr, text, error) {
			alert(xhr['responseText']);
		}
	});
	return $('<label>').append('Datensatz').append(ddbox);
}

/** renumber form field names after add/del of plot */
function renumber() {
	ch = $('#plots').children('.plot');
	ch.each(function(i) {
		plot = $(this);
		plot.find('legend').text('Plot ' + (i + 1));
		plot.find('[name]').each(function() {
			e = $(this);
			e.attr('name', e.attr('name').replace(/\*|\d/, '' + i));
		});
		plot.find(':button[name="delplot"]').attr('disabled', ch.length <= 1);
	});
	$(':button[name="addplot"]').attr('disabled', ch.length >= 4);
}

function isExpertmode() {
	return $(':input[name="expertmode"]:checked').size() > 0;
}

/** add interactive handlers */
function addhandlers(plot) {
	// display available vars on certain input fields
	plot
			.find(
					':input[name^="x"],:input[name^="y"],:input[name^="z"],:input[name^="c"]')
			.focusin(
					function() {
						p = $(this).parents('.plot');
						k = p.find('select[name^="s"]').val();
						$.each(tables_and_vars, function(kk, vv) {
							if (kk == k) {
								vars = $('#vars').empty();
								for (i = 0; i < vv[1].length; ++i) {
									if (i > 0)
										vars.append(', ');
									vars.append('' + vv[1][i]);
									if (vv[2][i].length > 0)
										vars.append(' [' + vv[2][i] + ']');
								}
								if (p.find(':input[name^="rw"]').val().replace(
										/\s+/, '') != '')
									vars.append(', rate, count');
								$('#varsbox').show();
								return false;
							}
						});
					}).focusout(function() {
				$('#varsbox').hide();
			});
	$('#varsbox').hide();

	// delete plot button
	plot.find(':button[name="delplot"]').click(function() {
		$(this).parents('.plot').remove();
		renumber();
	});

	// plot mode dropdown box
	plot.find(':input[name^="m"]').change(function() {
		ms = '.t-' + $(this).val();
		opt = $(this).parents('.plot').find('.opt');
		opt.not(ms).hide(speed).find(':input').attr('disabled', true);
		opt.filter(ms).show(speed).find(':input').attr('disabled', false);
	}).change();

	// rate window field
	plot.find(':input[name^="rw"]').keyup(
			function() {
				r = $(this).parents('.plot').find(
						':input[name^="rs"], :input[name^="rc"]');
				// if window empty:
				if ($(this).val().replace(/\s+/, '') == '') {
					r.attr('disabled', true);
					r.parent().hide(speed);
				} else if (isExpertmode()) {
					r.attr('disabled', false);
					r.parent().show(speed);
				}
			}).keyup();

	// twin axes dropdown box
	plot.find(':input[name^="tw"]').change(function() {
		hide_x = hide_y = true;
		$(':input[name^="tw"]').each(function() {
			if ($(this).val() == 'x')
				hide_x = false;
			if ($(this).val() == 'y')
				hide_y = false;
		});

		if (hide_x)
			$('.twinx').hide(speed);
		else
			$('.twinx').show(speed);

		if (hide_y)
			$('.twiny').hide(speed);
		else
			$('.twiny').show(speed);
	}).change();

	return plot;
}

/** Hilfe initialisieren */
function inithelp() {
	$('label[data-help]').each(
			function() {
				help = $(this).attr('data-help');
				$('<img>').attr('src', 'img/help.png').attr('title', help)
						.addClass('help').prependTo(this).hide();
			}).hover(function() {
		$(this).find('.help').show();
	}, function() {
		$(this).find('.help').hide();
	});
}

var xhr;

function initFormSubmit() {
	// hand submission of plot request and reception of the plot
	$('form')
			.submit(
					function() {
						try { // abort previous request
							xhr.abort();
						} catch (e) {
							// if there was no previous request, ignore errors
						}

						// the form (all input fields) as url query string
						query = $('form').serialize();

						// store current plot settings (all input fields) into
						// settings object
						settings = new Object();
						$(this)
								.find(
										':input:enabled:not(:button):not(:reset):not(:submit)[name][value]')
								.each(function() {
									if ($(this).is(':checkbox'))
										v = $(this).is(':checked');
									else
										v = $(this).val();
									settings[$(this).attr('name')] = v;

								});

						result = $('#result');
						// print status information
						result
								.empty()
								.append(
										'<p>Plot wird erstellt, bitte warten&hellip;</p><img src="img/bar90.gif">')
						// .append('<p>' + query + '</p>')
						;

						// scroll to plot section
						$('nav a[href="#output"]').click();

						// perform ajax request to get the plot (created on
						// server)
						$('#error').empty();
						xhr = $
								.ajax({
									data : query,
									success : function(data) {
										result.empty();
										$('<img>').attr(
												'src',
												data.png + '?'
														+ new Date().getTime()) // add
										// query
										// string
										// to
										// prevent
										// browser
										// from
										// showing
										// cached
										// image
										.attr('alt', query).appendTo(result);
										p = $('<p>').appendTo(result);
										p.append('Download als ');
										$('<a>').attr('href', data.pdf).attr(
												'target', '_blank').text('PDF')
												.appendTo(p);
										p.append(', ')
										$('<a>').attr('href', data.svg).attr(
												'target', '_blank').text('SVG')
												.appendTo(p);

										// plot settings
										result
												.append('<br>Einstellungen dieses Plots:<br>');
										result
												.append($(
														'<textarea id="plotsettings">')
														.text(
																JSON
																		.stringify(settings)));

										// plot url
										result
												.append('<br>Diesen Plot auf einer Webseite einbinden:<br>');
										ploturl = $(location).attr('href')
												.replace(/[#?].*/, '')
												+ 'webplot.py?'
												+ query.replace(/a=plot/,
														'a=png');
										result.append($(
												'<textarea id="ploturl">')
												.text(
														'<img src="' + ploturl
																+ '" />'));

										// scroll to plot section
										$('nav a[href="#output"]').click();
									},
									error : function(xhr, text, error) {
										$('#result').empty();
										$('#error')
												.html(
														'<p>plot error, check input values!</p>'
																+ '<p>"'
																+ text
																+ '"</p><p>"'
																+ error
																+ '"</p>'
																+ '<p style="color: red;">responseText:</p>'
																+ xhr['responseText']);
										// scroll to plot section
										$('nav a[href="#output"]').click();
									}
								});

						return false;
					});

}

/** on page load... */
$(function() {
	$.localScroll({
		hash : true
	});

	// detach navbar on scroll down
	$(window)
			.scroll(
					function() {
						scroll = $(this).scrollTop();
						nav = $('nav:not(.fixed)');
						if (nav.size() > 0)
							navoffset = nav.offset();
						if (scroll > navoffset.top) {
							$('nav').addClass('fixed').next().css('margin-top',
									$('nav').height());
						} else {
							$('nav').removeClass('fixed').next().css(
									'margin-top', '0');
						}

						pos = scroll + $('nav').height();
						$('nav a').removeClass('active').each(
								function() {
									target = $(this).attr('href');
									offset = $(target).offset();
									height = $(target).height();

									if (offset.top <= pos
											&& pos < offset.top + height) {
										$(this).addClass('active');
										return false;
									}
								})
					}).scroll();

	// set section size to viewport size
	$(window).resize(function() {
		$('#content > div').css('min-height', $(this).height());
	}).resize();

	// add source dropdown box to plot template, filled with available hdf5 data
	// files
	sourcesBox().prependTo('.plot');
	// detach the plot template (to be added by pressing 'add plot' button)
	plot = $('.plot').detach();

	// the 'add plot' button
	addbutton = $(':button[name="addplot"]');
	addbutton.click(function() {
		newplot = plot.clone()
		newplot.appendTo('#plots');
		renumber();
		addhandlers(newplot);
	}).click(); // add the first plot now

	inithelp();

	// add handler to expertmode checkbox
	$(':input[name="expertmode"]').click(function() {
		if ($(this).is(':checked')) {
			$('.expert').removeClass('hidden');
		} else {
			$('.expert').addClass('hidden');
		}
	});
	$(':input[name="expertmode"]:checked').click();
	$('.expert').addClass('hidden');

	initFormSubmit();

})