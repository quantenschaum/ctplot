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

var speed = 'fast';

/** add .startsWith() function to string */
if (typeof String.prototype.startsWith != 'function') {
	String.prototype.startsWith = function(str) {
		return this.indexOf(str) == 0;
	};
}

/** add .foreach() to arrays */
Array.prototype.foreach = function(callback) {
	for ( var k = 0; k < this.length; k++) {
		callback(k, this[k]);
	}
}

/** does browser support svg? */
function supportsSvg() {
	return document.implementation.hasFeature("http://www.w3.org/TR/SVG11/feature#Shape", "1.0")
}

var tables_and_vars = null;

/** get available HDF5 from server */
function sourcesBox() {
	var ddbox;
	$.ajax({
		async : false,
		data : {
			a : 'list'
		},
		success : function(data) {
			f = '';
			ddbox = $('<select>').attr('name', 's*');
			$('<option>').text('').val('').appendTo(ddbox);
			tables_and_vars = data;
			$.each(data, function(k, v) { // radiobutton for each
				coi = k.indexOf(':');
				file = k.substr(0, coi);
				tab = k.substr(coi + 1, k.length);
				opt = $('<option>').text(k.replace(/.*\/(.*)\.h5:(.*)/, '$1: ' + v[0])).val(k);
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
		plot.find(':button[name="delplot"]').prop('disabled', ch.length <= 1);
	});
	$(':button[name="addplot"]').prop('disabled', ch.length >= 4);
}

function isExpertmode() {
	return $(':checkbox[name="expertmode"]').prop('checked');
}

/** disable/enable fields according to expertmode and plotmode */
function updateHiddenFields() {
	expert = isExpertmode();
	if (!expert) // hide expert fields
		$('.expert').hide(speed).find(':input').prop('disabled', true);
	else {
		// twin axes global fields
		$.each([ 'x', 'y' ], function(i, v) {
			if ($(':input[name^="tw"][value="' + v + '"]').size() > 0)
				$('.twin' + v).show(speed).find(':input').prop('disabled', false);
			else
				$('.twin' + v).hide(speed).find(':input').prop('disabled', true);
		});
	}

	// field in individual plot settings
	$('.plot').each(function() {
		plot = $(this);
		plotmode = '.t-' + plot.find(':input[name^="m"]').val();
		opts = plot.find('.opt');
		opts.not(plotmode).hide(speed).find(':input').prop('disabled', true);
		if (expert) {
			opts.filter(plotmode).show(speed).find(':input').prop('disabled', false);
		} else {
			opts.filter(plotmode).not('.expert').show(speed).find(':input').prop('disabled', false);
		}
	});
}

/** add interactive handlers */
function addHandlers(plot) {
	// display available vars on certain input fields
	plot.find(':input[name^="x"],:input[name^="y"],:input[name^="z"],:input[name^="c"]').focusin(function() {
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
				if (p.find(':input[name^="rw"]').val().replace(/\s+/, '') != '')
					vars.append(', rate, count, weight');
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
		updateHiddenFields();
	}).change();

	// rate window field
	plot.find(':input[name^="rw"]').keyup(function() {
		r = $(this).parents('.plot').find(':input[name^="rs"], :input[name^="rc"]');
		// if window empty:
		if ($(this).val().replace(/\s+/, '') == '') {
			r.prop('disabled', true);
			r.parent().hide(speed);
		} else if (isExpertmode()) {
			r.prop('disabled', false);
			r.parent().show(speed);
		}
	}).keyup();

	// twin axes dropdown box
	plot.find(':input[name^="tw"]').change(function() {
		updateHiddenFields();
	}).change();

	return plot;
}

/** Hilfe initialisieren */
function initHelp() {
	$('label[data-help]').each(function() {
		help = $(this).attr('data-help');
		$('<img>').attr('src', 'img/help.png').attr('title', help).addClass('help').prependTo(this).hide();
	}).hover(function() {
		$(this).find('.help').show();
	}, function() {
		$(this).find('.help').hide();
	});
}

function getSettings() {
	s = new Object();
	$('form :input:enabled:not(:button):not(:reset):not(:submit)[name]').each(function() {
		field = $(this);
		name = field.attr('name');
		if (field.is(':checkbox')) {
			s[name] = field.prop('checked');
		} else {
			val = field.val();
			s[name] = field.val();
		}
	});
	s['plots'] = $('.plot').size();
	return s;
}

function setSettings(s) {
	$('.plot').remove();
	for ( var i = 0; i < s.plots; ++i)
		addPlot();
	$.each(s, function(k, v) {
		field = $(':input[name="' + k + '"]');
		if (field.is(':checkbox'))
			field.prop('checked', v);
		else
			field.val(v);
	});
	updateHiddenFields();
}

function initSettingsLoader() {
	$(':button[name="load"]').click(function() {
		try {
			s = JSON.parse($(':input[name="settingstoload"]').val());
			$('nav a[href="#settings"]').click();
			setSettings(s);
			// $('form').submit();
		} catch (e) {
			alert('Fehler beim Laden der Einstellungen: ' + e);
		}
	});
}

function initExpertMode() {
	// add handler to expertmode checkbox
	$(':checkbox[name="expertmode"]').click(updateHiddenFields);
	updateHiddenFields();
}

var templatePlot;

function initPlots() {
	// add source dropdown box to plot template, filled with available hdf5 data
	// files
	sourcesBox().prependTo('.plot');
	// detach the plot template (to be added by pressing 'add plot' button)
	templatePlot = $('.plot').detach();

	$(':button[name="addplot"]').click(addPlot);

	// try {
	// setSettings(JSON.parse($.cookie('lastsettings')));
	// } catch (e) {
	addPlot();
	// }

	loadPlots();
}

function addPlot() {
	if ($('.plot').size() == 0)
		newplot = templatePlot.clone()
	else
		newplot = $('.plot:first').clone();
	newplot.appendTo('#plots');
	renumber();
	addHandlers(newplot);
	updateHiddenFields();
}

function initScroll() {
	$.localScroll({
		hash : true
	});

	// detach navbar on scroll down
	$(window).scroll(function() {
		scroll = $(this).scrollTop();
		nav = $('nav:not(.fixed)');
		if (nav.size() > 0)
			navoffset = nav.offset();
		if (scroll > navoffset.top) {
			$('nav').addClass('fixed').next().css('margin-top', $('nav').height());
		} else {
			$('nav').removeClass('fixed').next().css('margin-top', '0');
		}

		pos = scroll + $('nav').height();
		$('nav a').removeClass('active').each(function() {
			target = $(this).attr('href');
			offset = $(target).offset();
			height = $(target).height();

			if (offset.top <= pos && pos < offset.top + height) {
				$(this).addClass('active');
				return false;
			}
		})
	}).scroll();

	// set section size to viewport size
	// $(window).resize(function() {
	// $('#content > div').css('min-height', $(this).height());
	// }).resize();
}

function getSessionID() {
	return 'abc123';
}

function savePlots() {
	o = new Object();
	o.savedPlots = [];
	$('#savedplots img').each(function() {
		o.savedPlots.push($(this).data('settings'));
	});
	$.ajax({
		// async : false,
		data : {
			a : 'save',
			id : getSessionID(),
			data : JSON.stringify(o)
		},
		dataType : 'text',
		// success : function(data, status, xhr) {
		// $('#debug').empty().append('' +
		// o).append('<br>').append(''+status).append('<br>').append(''+xhr);
		// },
		error : function(xhr, text, error) {
			alert('saving plots faild ' + text + ' ' + error);
		}
	});
}

function loadPlots() {
	$.ajax({
		// async : false,
		data : {
			a : 'load',
			id : getSessionID(),
		},
		dataType : 'json',
		success : function(o, status, xhr) {
			// $('#debug').empty().append('' + o).append('<br>').append('' +
			// status).append('<br>').append('' + xhr);
			$('#savedplots').empty();
			$.each(o.savedPlots, function(i, s) {
				addPlotToSaved(s);
			});
		},
	// error : function(xhr, text, error) {
	// alert('loading plots faild ' + text + ' ' + error);
	// }
	});
}

function addPlotToSaved(settings) {
	$('<img>').attr('src', settings.png).attr('alt', settings.t).attr('title', settings.t).data('settings', settings).appendTo('#savedplots').dblclick(
			function() {
				setSettings($(this).data('settings'));
				$('form').submit();
			});
}

var xhr;

function initSubmit() {
	// hand submission of plot request and reception of the plot
	$('form').submit(
			function() {
				try { // abort previous request
					xhr.abort();
				} catch (e) {
					// if there was no previous request, ignore errors
				}

				// the form (all input fields) as url query string
				query = $('form').serialize();
				settings = getSettings();

				// store current plot settings (all input fields) into
				// settings object

				result = $('#result');
				// print status information
				result.empty().append('<p>Plot wird erstellt, bitte warten&hellip;</p><img src="img/bar90.gif">')
				// .append('<p>' + query + '</p>')
				;

				// scroll to plot section
				// $('nav a[href="#output"]').click();

				// perform ajax request to get the plot (created on
				// server)
				$('#error').empty();
				xhr = $.ajax({
					data : query,
					success : function(data) {
						result.empty();
						$('<img>').attr('src', data.png + '?' + new Date().getTime())
						// add query string to prevent browser
						// from showing cached image
						.attr('alt', query).appendTo(result);

						// links to pdf and svg
						p = $('<p>').appendTo(result);
						p.append('Download als ');
						$('<a>').attr('href', data.pdf).attr('target', '_blank').text('PDF').appendTo(p);
						p.append(', ')
						$('<a>').attr('href', data.svg).attr('target', '_blank').text('SVG').appendTo(p);

						// store settings in cookie
						$.extend(settings, data); // append plot image urls to
						$.cookie('lastsettings', JSON.stringify(settings));
						// save plot button
						$('<input>').attr('type', 'button').attr('value', 'Plot speichern').click(function() {
							addPlotToSaved(settings);
							$(this).hide(speed);
							savePlots();
						}).appendTo(p);

						// plot settings
						result.append('<br>Einstellungen dieses Plots:<br>');
						jsonsettings = JSON.stringify(settings);
						result.append($('<textarea id="plotsettings">').text(jsonsettings));

						// plot url
						result.append('<br>Diesen Plot auf einer Webseite einbinden:<br>');
						ploturl = $(location).attr('href').replace(/[#?].*/, '') + 'webplot.py?' + query.replace(/a=plot/, 'a=png');
						result.append($('<textarea id="ploturl">').text('<img src="' + ploturl + '" />'));

						// scroll to plot section
						$('nav a[href="#output"]').click();
					},
					error : function(xhr, text, error) {
						$('#result').empty();
						$('#error').html(
								'<p>plot error, check input values!</p>' + '<p>"' + text + '"</p><p>"' + error + '"</p>'
										+ '<p style="color: red;">responseText:</p>' + xhr['responseText']);
						// scroll to plot section
						$('nav a[href="#output"]').click();
					}
				});

				return false;
			});
}

/** on page load... */
$(function() {
	initScroll();
	initPlots();
	initHelp();
	initExpertMode();
	initSubmit();
	initSettingsLoader();
});