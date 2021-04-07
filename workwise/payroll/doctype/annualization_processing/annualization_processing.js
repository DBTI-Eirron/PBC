// Copyright (c) 2019, HDI Systech and contributors
// For license information, please see license.txt

frappe.ui.form.on('Annualization Processing', {
	refresh: function(frm) {
		//Button Style
		document.querySelectorAll("[data-fieldname='process_annualization']")[1].style.backgroundColor ="#81da63";
		document.querySelectorAll("[data-fieldname='process_annualization']")[1].style.height ="30px";
		document.querySelectorAll("[data-fieldname='process_annualization']")[1].style.width ="150px";
		document.querySelectorAll("[data-fieldname='process_annualization']")[1].style.color ="white";
		
		frm.disable_save();

		frm.set_query("department", function() {
			return {
				"filters": {
					"company": frm.doc.company,
				}
			};
		});

		frm.set_query("employee", function() {
			return {
				"filters": {
					"company": frm.doc.company,
				}
			};
		});

		frm.set_query('period', function(doc) {
			return {
				filters: {
					"status": "Open",
					"is_special": 0,
					"company": doc.company
				}
			};
		});

		frm.set_query("location", function() {
			return {
				"filters": {
					"company": frm.doc.company,
				}
			};
		});
	},

	company: function(frm){
		frm.set_value("department", null);
		frm.set_value("location", null);
		frm.set_value("employee", null);
	}
});

cur_frm.cscript.display_activity_log = function(msg) {
	if(!cur_frm.ss_html)
		cur_frm.ss_html = $a(cur_frm.fields_dict['activity_log'].wrapper,'div');
	if(msg) {
		cur_frm.ss_html.innerHTML =
			'<div class="padding"><h4>'+__("Activity Log:")+'</h4>'+msg+'</div>';
	} else {
		cur_frm.ss_html.innerHTML = "";
	}
}

cur_frm.cscript.process_annualization = function(doc, cdt, cdn) {
	frappe.show_progress("Processing", 87, 100, "Processing Annualization");
	cur_frm.cscript.display_activity_log("");
	var callback = function(r, rt){
		if (r.message)
			frappe.hide_progress();
			cur_frm.cscript.display_activity_log(r.message);
	}
	return $c('runserverobj', args={'method':'process_annualization','docs':doc},callback);
}
