// Copyright (c) 2021, OSI and contributors
// For license information, please see license.txt

cur_frm.add_fetch('field', 'label', 'label');
cur_frm.add_fetch('field', 'fieldname', 'fieldname');
cur_frm.add_fetch('field', 'fieldtype', 'fieldtype');
cur_frm.add_fetch('field', 'options', 'options');

frappe.ui.form.on('Employee Movement Setup', {
	refresh: function(frm) {

	}
});

frappe.ui.form.on("Employee Movement Setup", "refresh", function(frm) {
    frm.fields_dict['fields'].grid.get_field('field').get_query = function(doc, cdt, cdn) {
        var child = locals[cdt][cdn];
        //console.log(child);
        return {    
            filters:[
                ['dt', '=', 'Employee'],
                ['fieldtype', 'not in', 'Attach, Attach Image, Button, Code, Color, Column Break, Dynamic Link, Geolocation, HTML, Section Break, Table, Signature']
            ]
        }
    }
});



