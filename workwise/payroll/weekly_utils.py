from __future__ import unicode_literals
import frappe, datetime
from datetime import time, datetime
from frappe.utils import cint, flt, nowdate, add_days, getdate, fmt_money
from frappe import _

def get_weekly_prev_map(employees, weekly_set):
	#Create Data Map
	data_map = frappe._dict()
	for emp in employees:
		data_map.setdefault(emp.name, frappe._dict({
				"previous_data": [],
			})
		)

	#Get Previous Data
	previous_data = frappe.db.sql(""" SELECT employee, frequency, government_basis, taxable_income, gross_payroll, 
		present_days, work_days, absent_days, govt_income, govt_deduction FROM `tabPayroll Register` 
		WHERE weekly_set = %s """,( weekly_set ), as_dict=True)

	for d in previous_data:
		if d.employee in data_map:
			data_map[d.employee].previous_data.append(d)

	return data_map

def get_weekly_basis(emp, header, govt_freq, curr_freq, weekly_data, current_basis):
	government_basis, prev_government_basis, govt_deduction, govt_income, monthly_basis = 0.0, 0.0, 0.0, 0.0, 0.0
	no_weeks =  header.get('no_weeks')
	weekly_targets = get_weekly_targets(govt_freq, curr_freq, no_weeks)
	
	if emp.get('name') in weekly_data:
		for d in weekly_data[emp.get('name')].previous_data:
			if d.frequency in weekly_targets:
				prev_government_basis += d.government_basis
				govt_deduction += d.govt_deduction
				govt_income += d.govt_income

			if d.frequency != "5th":
				monthly_basis += d.government_basis

	if govt_freq == "2nd":
		if no_weeks == "5" and curr_freq == "5th":
			government_basis = current_basis + prev_government_basis
		
		elif curr_freq == "4th":
			government_basis = current_basis + prev_government_basis

	elif govt_freq == "Both":
		if curr_freq == "2nd":
			government_basis = current_basis + prev_government_basis

		elif no_weeks == "4" and curr_freq == "4th" or curr_freq == "5th":
			government_basis = current_basis + prev_government_basis								

		elif no_weeks == "5" and curr_freq == "5th":
			government_basis = current_basis + prev_government_basis
	
	elif govt_freq == "All":
		government_basis = current_basis

	if monthly_basis:
		monthly_basis += current_basis
		
	return government_basis, monthly_basis

def get_weekly_targets(govt_freq, curr_freq, no_weeks):
	targets = []
	if govt_freq == "2nd":
		if no_weeks == "5":
			targets = ["1st","2nd","3rd","4th"]
		else:
			targets = ["1st","2nd","3rd"]

	elif govt_freq == "Both":
		if curr_freq == "2nd":
			targets = "1st"

		elif no_weeks == "4" and curr_freq == "4th":
			targets = ["3rd"]

		elif no_weeks == "5" and curr_freq == "5th":
			targets = ["3rd","4th"]					

	return targets



