# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

from __future__ import unicode_literals
import frappe
import re
from frappe import _
from frappe.utils import (flt, getdate, get_first_day, get_last_day, date_diff,
	add_months, add_days, formatdate, cint)

def execute(filters=None):
	position_list = get_position_list(filters)
	roots = frappe.db.sql("""select name, lft, rgt from tabDepartment where is_group = 1 ORDER BY lft """, as_dict=1)
	
	data = []
	net_total_row = {
		"department_name": "'" + _("Net Total") + "'",
		"department": "'" + _("Total") + "'",
		"warn_if_negative": True,
	}

	for position in position_list:
		net_total_row[position.key] = 0.0
	
	total_target = 0.0
	total_actual = 0.0
	for root in roots:
		data += get_data(filters.company, root.name, position_list, filters=filters,
			accumulated_values=True, ignore_closing_entries=True, ignore_accumulated_values_for_fy=True)
		
		for position in position_list:
			temp_total = flt(data[-2][position.key], 3) if data else 0
			if position.key == "Target":
				net_total_row[position.key] += temp_total
				total_target += temp_total
			else:
				net_total_row[position.key] += temp_total
				total_actual += temp_total
	
	
	net_total_row["total_actual"] = total_actual
	net_total_row["total_variance"] = total_actual - total_target
	data.append(net_total_row)

	columns = get_columns(position_list, filters.accumulated_values, filters.company)
	return columns, data, None, None

def get_position_list(filters):
	positions = frappe.db.sql(""" SELECT `name` as `key`, CONCAT(`name`,"-",level_no) as `label` FROM `tabJob Level` ORDER BY level_no DESC""", as_dict=True)
	positions.append(frappe._dict({
		"key": "Target",
		"label": "Target",
	}))

	#frappe.throw(_(positions))
	return positions

def get_departments(filters):
	return frappe.db.sql("""select name, parent_department, lft, rgt, department_name from `tabDepartment` order by lft""", as_dict=True)

def filter_departments(departments, depth=10):
	parent_children_map = {}
	departments_by_name = {}
	for d in departments:
		departments_by_name[d.name] = d
		parent_children_map.setdefault(d.parent_department or None, []).append(d)

	filtered_departments = []

	def add_to_list(parent, level):
		if level < depth:
			children = parent_children_map.get(parent) or []
			if parent == None:
				children

			for child in children:
				child.indent = level
				filtered_departments.append(child)
				add_to_list(child.name, level + 1)

	add_to_list(None, 0)

	return filtered_departments, departments_by_name, parent_children_map

def set_emp_entries_by_department(company, as_of_date, root_lft, root_rgt, filters, emp_entries_by_department, ignore_closing_entries=False):

	emp_entries = frappe.db.sql("""select department, job_level as position_title, count(`name`) as qty from `tabEmployee`
		where 
		company=%(company)s
		and is_active = 1
		and department in (select name from `tabDepartment` where lft >= %(lft)s and rgt <= %(rgt)s)
		group by department, job_level
		order by department """,
		{
			"company": company,
			"as_of_date": as_of_date,
			"lft": root_lft,
			"rgt": root_rgt
		},
		as_dict=True)

	emp_entries += frappe.db.sql("""select department, "Target" as position_title, SUM(quantity) as qty from `tabTalent Requisition`
		where company=%(company)s
		and department in (select name from `tabDepartment` where lft >= %(lft)s and rgt <= %(rgt)s)
		and docstatus = 1
		group by department
		order by department """,
		{
			"company": company,
			"as_of_date": as_of_date,
			"lft": root_lft,
			"rgt": root_rgt
		},
		as_dict=True)

	for entry in emp_entries:
		emp_entries_by_department.setdefault(entry.department, []).append(entry)

	return emp_entries_by_department


def get_data(company, root_name, position_list, filters=None, accumulated_values=1, only_current_fiscal_year=True, ignore_closing_entries=False, ignore_accumulated_values_for_fy=False):
	departments = get_departments(filters)
	if not departments:
		return None

	departments, departments_by_name, parent_children_map = filter_departments(departments)

	emp_entries_by_department = {}
	
	for root in frappe.db.sql("""select lft, rgt from tabDepartment where `name` = %s and is_group = 1 """, root_name,as_dict=1):
		set_emp_entries_by_department(filters.company, filters.as_of_date, root.lft, root.rgt, filters, emp_entries_by_department, ignore_closing_entries=ignore_closing_entries)

	calculate_values(departments_by_name, emp_entries_by_department, position_list, accumulated_values, ignore_accumulated_values_for_fy)
	accumulate_values_into_parents(departments, departments_by_name, position_list, accumulated_values)
	out = prepare_data(company, departments, position_list)
	out = filter_out_zero_value_rows(out, parent_children_map)

	if out:
		add_total_row(out, root_name, position_list)

	return out

def calculate_values(departments_by_name, emp_entries_by_department, position_list, accumulated_values, ignore_accumulated_values_for_fy):
	for entries in emp_entries_by_department.values():
		for entry in entries:
			d = departments_by_name.get(entry.department)
			if not d:
				frappe.msgprint(
					_("Could not retrieve information for {0}.".format(entry.department)), title="Error",
					raise_exception=1
				)
			for position in position_list:
				if entry.position_title == position.key:
					d[position.key] = d.get(position.key, 0.0) + flt(entry.qty, 8)

			#if entry.posting_date < period_list[0].year_start_date:
			#	d["opening_balance"] = d.get("opening_balance", 0.0) + flt(entry.debit) - flt(entry.credit)

def accumulate_values_into_parents(departments, departments_by_name, position_list, accumulated_values):
	for d in reversed(departments):
		if d.parent_department:
			for position in position_list:
				departments_by_name[d.parent_department][position.key] = \
					departments_by_name[d.parent_department].get(position.key, 0.0) + d.get(position.key, 0.0)

			#accounts_by_name[d.parent_account]["opening_balance"] = \
			#	accounts_by_name[d.parent_account].get("opening_balance", 0.0) + d.get("opening_balance", 0.0)

def prepare_data(company, departments, position_list):
	data = []

	for d in departments:
		has_value = False
		total_variance = 0
		total_actual = 0
		total_target = 0

		row = frappe._dict({
			"department_name": _(d.department_name),
			"department": _(d.name),
			"parent_department": _(d.parent_department),
			"indent": flt(d.indent),
		})
		for position in position_list:
			row[position.key] = flt(d.get(position.key, 0.0), 3)

			if abs(row[position.key]) >= 0.005:
				# ignore zero values
				has_value = True

				if position.key == "Target":
					total_target += flt(row[position.key])
				else:
					total_actual += flt(row[position.key])

		row["has_value"] = has_value
		row["total_actual"] = total_actual
		row["total_variance"] = total_actual - total_target

		data.append(row)

	return data

def filter_out_zero_value_rows(data, parent_children_map, show_zero_values=False):
	data_with_value = []
	for d in data:
		if show_zero_values or d.get("has_value"):
			data_with_value.append(d)
		else:
			# show group with zero balance, if there are balances against child
			children = [child.name for child in parent_children_map.get(d.get("account")) or []]
			if children:
				for row in data:
					if row.get("account") in children and row.get("has_value"):
						data_with_value.append(d)
						break

	return data_with_value

def add_total_row(out, root_name, position_list):
	total_row = {
		"department_name": "'" + _("Total {0} ").format(_(root_name)) + "'",
		"department": "'" + _("Total {0} ").format(_(root_name)) + "'",
	}

	for row in out:
		if not row.get("parent_department"):
			total_variance = 0.0
			total_target = 0.0
			total_actual = 0.0
			
			for period in position_list:
				total_row.setdefault(period.key, 0.0)
				if period.key == "Target":
					total_target += row.get(period.key, 0.0)
				else:
					total_actual += row.get(period.key, 0.0)

				total_row[period.key] += row.get(period.key, 0.0)
				row[period.key] = None

			total_row.setdefault("total_actual", 0.0)
			total_row.setdefault("total_variance", 0.0)

			total_row["total_actual"] += total_actual
			total_row["total_variance"] += (total_actual - total_target)

			row["total_actual"] = ""
			row["total_variance"] = ""

	if total_row.has_key("total_actual"):
		out.append(total_row)

		# blank row after Total
		out.append({})

def get_requisition(company, lft, rgt):
	total = 0.0
	requisition_entries = frappe.db.sql("""select sum(quantity) as qty from `tabPersonnel Requisition`
		where company=%(company)s
		and docstatus = 1
		and department in (select name from `tabDepartment` where lft >= %(lft)s and rgt <= %(rgt)s)
		order by department """,
		{
			"company": company,
			"lft": lft,
			"rgt": rgt
		}, as_dict=True)

	for d in requisition_entries:
		total += flt(d.qty, 8)

	return total

def get_columns(position_list, accumulated_values=1, company=None):
	columns = [{
		"fieldname": "department",
		"label": _("Department"),
		"fieldtype": "Link",
		"options": "Department",
		"width": 300
	}]
	for position in position_list:
		columns.append({
			"fieldname": position.key,
			"label": position.label,
			"fieldtype": "Int",
			"width": 100
		})

	columns.append({
		"fieldname": "total_actual",
		"label": _("Actual"),
		"fieldtype": "Int",
		"width": 80
	})

	columns.append({
		"fieldname": "total_variance",
		"label": _("Variance"),
		"fieldtype": "Int",
		"width": 80
	})
	return columns
