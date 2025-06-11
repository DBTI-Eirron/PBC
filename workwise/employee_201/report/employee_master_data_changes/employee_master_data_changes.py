# Copyright (c) 2013, OSI and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _

def execute(filters=None):
	columns = get_columns(filters)
	results = get_result(filters)
	 
	return columns, results

def get_columns(filters):
	columns = [
		{
			"fieldname": "movement_type",
			"label": _("Movement Type"),
			"fieldtype": "Data",
			"width": 140
		},
		{
			"fieldname": "employee",
			"label": _("Employee"),
			"fieldtype": "Data",
			"width": 140
		},
		{
			"fieldname": "employee_name",
			"label": _("Employee Name"),
			"fieldtype": "Data",
			"width": 200
		},
		{
			"fieldname": "effective_on",
			"label": _("Effective On"),
			"fieldtype": "Date",
			"width": 120
		},
		{
			"fieldname": "new_employee_name",
			"label": _("New Employee Name"),
			"fieldtype": "Data",
			"width": 150
		},
		{
			"fieldname": "transfer_type",
			"label": _("Transfer Type"),
			"fieldtype": "Data",
			"width": 120
		},
		{
			"fieldname": "current_rate",
			"label": _("Current Rate"),
			"fieldtype": "Data",
			"width": 120
		},
		{
			"fieldname": "new_rate",
			"label": _("New Rate"),
			"fieldtype": "Data",
			"width": 120
		},
		{
			"fieldname": "current_position",
			"label": _("Current Position Title"),
			"fieldtype": "Data",
			"width": 120
		},
		{
			"fieldname": "new_position",
			"label": _("New Position Title"),
			"fieldtype": "Data",
			"width": 120
		},
		{
			"fieldname": "current_bank_details",
			"label": _("Current Bank Details"),
			"fieldtype": "Data",
			"width": 120
		},
		{
			"fieldname": "new_bank_details",
			"label": _("New Bank Details"),
			"fieldtype": "Data",
			"width": 120
		},
		{
			"fieldname": "prepared_by_name",
			"label": _("Created By"),
			"fieldtype": "Data",
			"width": 200
		},
		{
			"fieldname": "checked_by_name",
			"label": _("Checked By"),
			"fieldtype": "Data",
			"width": 200
		},
		{
			"fieldname": "approved_by_name",
			"label": _("Approved By"),
			"fieldtype": "Data",
			"width": 200
		}
	]
	return columns

def get_result(filters):
	data = get_data(filters)
	return data

def get_data(filters):
	data = []
	
	try:

		payroll_period = frappe.get_doc("Payroll Period", filters.get("payroll_period"))
		from_date = payroll_period.start_date
		to_date = payroll_period.end_date

		employees = frappe.db.sql("""
				SELECT 
					EM.docstatus,
					EM.movement_type,
					EM.employee,
					EM.employee_name,
					EM.effective_on,
					EM.new_first_name,
					EM.new_middle_name,
					EM.new_last_name,
					EM.old_first_name,
					EM.old_middle_name,
					EM.old_last_name,
					EM.transfer_type,
					EM.current_rate,
					EM.new_rate,
					EM.transfer_cur_position_title,
					EM.transfer_new_position_title,
					EM.current_position,
					EM.new_position,
					GROUP_CONCAT(DISTINCT 
						CASE 
							WHEN NBI.account_type = 'Primary' THEN CONCAT(NBI.bank_account, ' (Primary)')
							ELSE NBI.bank_account
						END SEPARATOR ', ') AS new_bank_accounts,

					GROUP_CONCAT(DISTINCT 
						CASE 
							WHEN OBI.account_type = 'Primary' THEN CONCAT(OBI.bank_account, ' (Primary)')
							ELSE OBI.bank_account
						END SEPARATOR ', ') AS old_bank_accounts,
					EM.prepared_by_name,
					EM.checked_by_name,
					EM.approved_by_name,
					IFNULL(CONCAT(E.first_name, ' ', IFNULL(E.middle_name, ''), ' ', E.last_name), '') AS prepared_by_name,
					IFNULL(CONCAT(F.first_name, ' ', IFNULL(F.middle_name, ''), ' ', F.last_name), '') AS checked_by_name,
					IFNULL(CONCAT(G.first_name, ' ', IFNULL(G.middle_name, ''), ' ', G.last_name), '') AS approved_by_name
				FROM `tabEmployee Movement` EM
				LEFT JOIN `tabNew Bank Information` NBI ON EM.name = NBI.parent
				LEFT JOIN `tabOld Bank Information` OBI ON EM.name = OBI.parent
				LEFT JOIN `tabEmployee` E ON EM.created_by = E.name
				LEFT JOIN `tabEmployee` F ON EM.checked_by = F.name
				LEFT JOIN `tabEmployee` G ON EM.approved_by = G.name
				WHERE EM.effective_on BETWEEN %(from_date)s AND %(to_date)s AND EM.docstatus = 1
				AND EM.movement_type = %(movement_type)s
				GROUP BY EM.name
				ORDER BY EM.effective_on ASC
			""", {
				"from_date": from_date,
    			"to_date": to_date,
				"movement_type": filters.get("movement_type")
			}, as_dict=True)
	
		for employee in employees:
			display_name = ""
			transfer_type = ""
			current_rate = ""
			new_rate = ""
			current_position = ""
			new_position = ""
			current_bank_details = ""
			new_bank_details = ""
			created_by = ""
			checked_by = ""
			approved_by = ""
			
			# Special handling for "Change of Name" movement type
			if employee.get("movement_type") == "Change of Name":
				display_name = get_change_of_name_display(employee)
			
			if employee.get("movement_type") == "Transfer":
				transfer_type = employee.get("transfer_type")
				current_position = employee.get("transfer_cur_position_title")
				new_position = employee.get("transfer_new_position_title")
			
			if employee.get("movement_type") == "Salary Adjustment" or employee.get("movement_type") == "Job Rotation" or employee.get("movement_type") == "Transfer" or employee.get("movement_type") == "Regularization" or employee.get("Promotion"):
				current_rate = employee.get("current_rate")
				new_rate = employee.get("new_rate")
			
			if employee.get("movement_type") == "Job Rotation":
				current_position = employee.get("current_position")
				new_position = employee.get("new_position")
			
			# if movement type is "Change Bank Details" do comma separate the bank accounts
			if employee.get("movement_type") == "Change Bank Details":
				new_bank_details = employee.get("new_bank_accounts")
				current_bank_details = employee.get("old_bank_accounts")

			if employee.get("movement_type") == "Add Bank Details":
				new_bank_details = employee.get("new_bank_accounts")

			created_by = employee.get("prepared_by_name")

			if employee.get("movement_type") == "Salary Adjustment":
				checked_by = employee.get("checked_by_name")
				approved_by = employee.get("approved_by_name")
			
			entry = {
				"movement_type": employee.get("movement_type"),
				"employee": employee.get("employee"),
				"employee_name": employee.get("employee_name"),
				"effective_on": employee.get("effective_on"),
				"new_employee_name": display_name,
				"transfer_type": transfer_type,
				"current_rate": current_rate,
				"new_rate": new_rate,
				"current_position": current_position,
				"new_position": new_position,
				"current_bank_details": current_bank_details,
				"new_bank_details": new_bank_details,
				"prepared_by_name": created_by,
				"checked_by_name": checked_by,
				"approved_by_name": approved_by
			}

			data.append(entry)

	except Exception as e:
		frappe.msgprint("Error in SQL query: {0}".format(str(e)))
		
	return data

def get_change_of_name_display(employee_data):
	"""
	Format name for Change of Name movement type
	Format: First Name Middle Initial Last Name
	If only last name changed, use old first and middle name
	"""
	# Get new name components
	new_first = employee_data.get("new_first_name")
	new_middle = employee_data.get("new_middle_name") 
	new_last = employee_data.get("new_last_name")
	
	# Get current/old name components
	old_first = employee_data.get("old_first_name")
	old_middle = employee_data.get("old_middle_name")
	old_last = employee_data.get("old_last_name")
	
	# Determine which names to use
	first_name = new_first if new_first else old_first
	middle_name = new_middle if new_middle else old_middle
	last_name = new_last if new_last else old_last
	
	# Format the display name
	display_parts = []
	
	# Add first name
	if first_name:
		display_parts.append(first_name)
	
	# Add middle initial (first letter of middle name + period)
	if middle_name:
		middle_initial = middle_name[0].upper() + "."
		display_parts.append(middle_initial)
	
	# Add last name
	if last_name:
		display_parts.append(last_name)
	
	return " ".join(display_parts) if display_parts else employee_data.get("employee_name", "")