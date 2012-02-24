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
	url : 'web.py',
	dataType : 'json'
});

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

var tables_and_vars=null;

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
			$('<option>').text('').val('').appendTo(
					ddbox);
			tables_and_vars=data;
			$.each(data, function(k, v) { // radiobutton for each
				coi = k.indexOf(':');
				file = k.substr(0, coi);
				tab = k.substr(coi + 1, k.length);
				opt = $('<option>').text(k.replace(/.*\/(.*)\.h5:(.*)/, '$1: '+v[0])).val(k);
				if(isExpertmode() || !opt.text().startsWith('x'))
					opt.appendTo(ddbox);
				$('#debug').append(k).append(v[0]).append('<br>');
			});
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
	plot.find(':input[name^="x"],:input[name^="y"],:input[name^="z"],:input[name^="c"]')
		.focusin(function(){
			p=$(this).parents('.plot');
			k=p.find('select[name^="s"]').val();
			$.each(tables_and_vars, function(kk,vv){
				if(kk==k){
					vars = $('#vars').empty();
					for (i = 0; i < vv[1].length; ++i) {
						if (i > 0)
							vars.append(', ');
						vars.append('' + vv[1][i]);
						if (vv[2][i].length > 0)
							vars.append(' [' + vv[2][i] + ']');
					}
					if (p.find(':input[name^="rw"]').val().replace(/\s+/, '') != '')
						vars.append(', rate, count');
					$('#varsbox').show();
					return false;
				}
			});
		}).focusout(function(){
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
		if (!isExpertmode()) {
			opt.filter('.expert').hide();
			opt = opt.not('.expert');
		}
		opt.not(ms).hide('slow').find(':input').attr('disabled', true);
		opt.filter(ms).show('slow').find(':input').attr('disabled', false);
	}).change();

	// rate window field
	plot.find(':input[name^="rw"]').keyup(
			function() {
				r = $(this).parents('.plot').find(
						':input[name^="rs"], :input[name^="rc"]');
				// if window empty:
				if ($(this).val().replace(/\s+/, '') == '') {
					r.attr('disabled', true);
					r.parent().hide('slow');
				} else if (isExpertmode()) {
					r.attr('disabled', false);
					r.parent().show('slow');
				}
			}).keyup();

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
						// $('#debug').text(
						// JSON.stringify(navoffset) + ', ' + scroll
						// + ', '
						// + JSON.stringify($('nav').offset()));
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

	// hand submission of plot request and reception of the plot
	$('form')
			.submit(
					function() {
						// the form (all input fields) as url query string
						query = $('form').serialize();

						// store current plot settings (all input fields) into
						// settings object
						settings = new Object();
						$(this)
								.find(
										':input:enabled:not(:button):not(:reset):not(:submit)[name][value]')
								.each(
										function() {
											settings[$(this).attr('name')] = $(
													this).val();

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
						$.ajax({
									data : query,
									success : function(data) {
										result.empty();
										$('<img>').attr('src', data.png).appendTo(result);
										p=$('<p>').appendTo(result);
										p.append('Download als ');
										$('<a>').attr('href', data.pdf).text('PDF').appendTo(p);
										p.append(', ')
										$('<a>').attr('href', data.svg).text('SVG').appendTo(p);
										result.append($('<p>').text('plot settings: '+JSON.stringify(settings)));
									},
									error : function(xhr, text, error) {
										$('#result').empty();
										$('#error')
												.html('<p>plot error, check input values!</p>'
														+ '<p>"'
														+ text
														+ '"</p><p>"'
														+ error
														+ '"</p>'
														+ '<p style="color: red;">responseText:</p>'
														+ xhr['responseText']);
									}
								});

						return false;
					});
})