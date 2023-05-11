/*
 * Context.js
 * Copyright Jacob Kelley
 * MIT License
 * http://lab.jakiestfu.com/contextjs/context.js
 */

var context = context || (function () {

	var options = {
		fadeSpeed: 100,
		filter: function ($obj) {
			// Modify $obj, Do not return
		},
		above: 'auto',
		preventDoubleContext: true,
		compress: false
	};

	function initialize(opts) {

		options = $.extend({}, options, opts);

		$(document).on('click', 'html', function () {
			$('.dropdown-context').fadeOut(options.fadeSpeed, function(){
				$('.dropdown-context').css({display:''}).find('.drop-left').removeClass('drop-left');
			});
		});
		if(options.preventDoubleContext){
			$(document).on('contextmenu', '.dropdown-context', function (e) {
				e.preventDefault();
			});
		}
		$(document).on('mouseenter', '.dropdown-submenu', function(){
			var $sub = $(this).find('.dropdown-context-sub:first'),
				subWidth = $sub.width(),
				subLeft = $sub.offset().left,
				collision = (subWidth+subLeft) > window.innerWidth;
			if(collision){
				$sub.addClass('drop-left');
			}
		});

	}

	function updateOptions(opts){
		options = $.extend({}, options, opts);
	}

	function buildMenu(data, id, subMenu) {
		var subClass = (subMenu) ? ' dropdown-context-sub' : '';
		var compressed = options.compress ? ' compressed-context' : '';
		var $menu = $('<div class="dropdown-menu dropdown-context' + subClass + compressed+'" id="dropdown-' + id + '"></div>');
        var i = 0, linkTarget = '';
        for(i; i<data.length; i++) {
			var disabled = data[i].disabled ? ' disabled': '';
        	if (typeof data[i].divider !== 'undefined') {
				$menu.append('<div class="dropdown-divider"></div>');
			} else if (typeof data[i].header !== 'undefined') {
				$menu.append('<h6 class="dropdown-header">' + data[i].header + '</h6>');
			} else {
				if (typeof data[i].href == 'undefined') {
					data[i].href = '#';
				}
				if (typeof data[i].target !== 'undefined') {
					linkTarget = ' target="'+data[i].target+'"';
				}
				if (typeof data[i].subMenu !== 'undefined') {
					$sub = $('<li class="dropdown-submenu"><a class="dropdown-item' + disabled + '" tabindex="-1" href="' + data[i].href + '">' + data[i].text + '</a></li>');
				} else {
					$sub = $('<li><a class="dropdown-item' + disabled + '" tabindex="-1" href="' + data[i].href + '"'+linkTarget+'>' + data[i].text + '</a></li>');
				}
				if (typeof data[i].action !== 'undefined') {
					var action_date = new Date();
					var action_id = 'event-' + action_date.getTime() * Math.floor(Math.random()*100000);
					var event_action = data[i].action;

					$sub.find('a').attr('id', action_id);
					$('#' + action_id).addClass('context-event');
					(function(eventAction) {
						$(document).on('click', '#' + action_id, function(event) {
							eventAction(event, $menu.context);
						});
					})(event_action);
				}
				$menu.append($sub);
				if (typeof data[i].subMenu != 'undefined') {
					var subMenuData = buildMenu(data[i].subMenu, id, true);
					$menu.find('li:last').append(subMenuData);
				}
			}
			if (typeof options.filter == 'function') {
				options.filter($menu.find('li:last'));
			}
		}
		return $menu;
	}

	function addContext(selector, data) {

		var date = new Date();
		var id = date.getTime() * Math.floor(Math.random()*100000);;
		var $menu = buildMenu(data, id);

		$('body').append($menu);

		$(document).on('contextmenu', selector, function (e) {
			e.preventDefault();
			e.stopPropagation();
			$menu.context = this;

			$('.dropdown-context:not(.dropdown-context-sub)').hide();

			$dd = $('#dropdown-' + id);
			if (typeof options.above == 'boolean' && options.above) {
				$dd.addClass('dropdown-context-up').css({
					top: e.pageY - 20 - $('#dropdown-' + id).height(),
					left: e.pageX - 13
				}).fadeIn(options.fadeSpeed);
			} else if (typeof options.above == 'string' && options.above == 'auto') {
				$dd.removeClass('dropdown-context-up');
				var autoH = $dd.height() + 12;
				if ((e.pageY + autoH) > $('html').height()) {
					$dd.addClass('dropdown-context-up').css({
						top: e.pageY - 20 - autoH,
						left: e.pageX - 13
					}).fadeIn(options.fadeSpeed);
				} else {
					$dd.css({
						top: e.pageY + 10,
						left: e.pageX - 13
					}).fadeIn(options.fadeSpeed);
				}
			}
		});
	}

	function destroyContext(selector) {
		$(document).off('contextmenu', selector).off('click', '.context-event');
	}

	return {
		init: initialize,
		settings: updateOptions,
		attach: addContext,
		destroy: destroyContext
	};
})();