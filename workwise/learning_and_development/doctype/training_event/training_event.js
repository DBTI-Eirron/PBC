// Copyright (c) 2017, HDI Systech and contributors
// For license information, please see license.txt

cur_frm.add_fetch('employee', 'position_title', 'position_title');
cur_frm.add_fetch('employee', 'department', 'department');
cur_frm.add_fetch('employee', 'division', 'division');

frappe.ui.form.on('Training Event', {
	refresh: function(frm) {

	},

	course: function(frm) {
		frm.trigger("get_description"); 
	},

	get_description: function(frm) {
		if(frm.doc.course) {
	 		return frappe.call({
				method: "workwise.hr.doctype.training_event.training_event.get_description",
				args: {
					source_value: frm.doc.course,
				},
				callback: function(r) {
					if (!r.exc && r.message) {
						frm.set_value("description", r.message.target_description);
					}
				}
			});
		}
	},

	number_of_attendees: function(frm) {
		frm.trigger("get_calculated_total_cost"); 
	},

	cost_per_participant: function(frm) {
		frm.trigger("get_calculated_total_cost"); 
	},	

	get_calculated_total_cost: function(frm) {
		if( frm.doc.number_of_attendees && frm.doc.cost_per_participant) {
    		return frappe.call({
				method: "workwise.hr.doctype.training_event.training_event.get_total_cost",
				args: {
					number_of_attendees: frm.doc.number_of_attendees,
					cost_per_participant: frm.doc.cost_per_participant,
				},
				callback: function(r) {
					if (!r.exc && r.message) {
						frm.set_value("total_cost", r.message.target_total_cost);
					}
				}
			});	
		}
	},
});

frappe.ui.form.on('Training Attendees', {
    training_attendees_add: function(frm) {
    	total = frm.doc.number_of_attendees;
		total += 1;
		frm.set_value("number_of_attendees", total);
    },

    training_attendees_remove: function(frm) {
    	total = frm.doc.number_of_attendees;
		total -= 1;
		frm.set_value("number_of_attendees", total);
    }
});