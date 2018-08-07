frappe.provide('workwise');

$(document).bind('toolbar_setup', function() {
	frappe.call({
		method: "workwise.employee_201.doctype.company.company.get_company_logo",
		args: {
			user: frappe.session.user
		},
		callback: function(r) {
			if(!r.exc) {
				if(r.message) {
					$('.navbar-home').html('<img style="max-height:25px;" class="" src="'+frappe.urllib.get_base_url()+''+r.message+'" />');
				}
			}
		}
	});

});
frappe.ui.set_user_background = function(src, selector, style) {
	if(!selector) selector = "#page-desktop";
	if(!style) style = "Fill Screen";
	if(src) {
		if (window.cordova && src.indexOf("http") === -1) {
			src = frappe.base_url + src;
		}
		var background = repl('background: url("%(src)s") center center;', {src: src});
	} else {
		var background = "background-color: #f2f2f2;";
	}

	frappe.dom.set_style(repl('%(selector)s { \
		%(background)s \
		background-attachment: fixed; \
		%(style)s \
	}', {
		selector:selector,
		background:background,
		style: style==="Fill Screen" ? "background-size: cover;" : ""
	}));
}
