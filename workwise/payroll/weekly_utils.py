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
	previous_data = frappe.db.sql(""" SELECT employee, frequency, govt_basic as government_basis, taxable_income, gross_payroll, 
		present_days, work_days, absent_days, govt_income, govt_deduction, 
		sss_inc, 
		sss_ded, 
		sss_amt as sss, 
		sss_er_amt as ssse, 
		sss_ec_amt as sssc,
		sss_ee_mpf,
		sss_er_mpf,
		phic_inc,
		phic_ded, 
		phic_amt as phic, 
		phic_er_amt as phice, 
		phic_ec_amt as phicc,
		hdmf_inc, 
		hdmf_ded, 
		hdmf_amt as hdmf, 
		hdmf_er_amt as hdmfe, 
		hdmf_ec_amt as hdmfc, 
		hdmf_manual as hdmfm
		FROM `tabPayroll Register` 
		WHERE weekly_set = %s """,( weekly_set ), as_dict=True)

	for d in previous_data:
		if d.employee in data_map:
			data_map[d.employee].previous_data.append(d)

	return data_map

def get_weekly_basis(govt_type, emp, header, govt_freq, curr_freq, weekly_data, current_basis):
	government_basis, prev_government_basis, govt_deduction, govt_income, monthly_basis = 0.0, 0.0, 0.0, 0.0, 0.0
	weekly_previous_amts = {}
	sss, ssse, sssc, sss_ee_mpf, sss_er_mpf = 0.0, 0.0, 0.0, 0.0, 0.0 #used for getting sss data an all previous frequencies
	no_weeks =  header.get('no_weeks')
	weekly_targets = get_weekly_targets(govt_freq, curr_freq, no_weeks)
	test = []
	if emp.get('name') in weekly_data:
		for d in weekly_data[emp.get('name')].previous_data:
			if d.frequency in weekly_targets:
				test.append(_( ("{0}:{1}").format(d.frequency, ((d.government_basis + d.govt_income) - d.govt_deduction) ) ))
				prev_government_basis += d.government_basis
				govt_deduction += d.govt_deduction
				govt_income += d.govt_income

				freq_passed = 0
				if no_weeks in ["1", 1]:
					if d.frequency in ['1st']:
						freq_passed = 1
				if no_weeks in ["2", 2]:
					if d.frequency in ['1st', '2nd']:
						freq_passed = 1
				if no_weeks in ["3", 3]:
					if d.frequency in ['1st', '2nd', '3rd']:
						freq_passed = 1
				if no_weeks in ["4", 4]:
					if d.frequency in ['1st', '2nd', '3rd', '4th']:
						freq_passed = 1
				if no_weeks in ["5", 5]:
					if d.frequency in ['1st', '2nd', '3rd', '4th', '5th']:
						freq_passed = 1

				if freq_passed:
					sss += d.sss
					ssse += d.ssse
					sssc += d.sssc
					sss_ee_mpf += d.sss_ee_mpf
					sss_er_mpf += d.sss_er_mpf

					if govt_type == 'sss':
						prev_government_basis += d.sss_inc
						prev_government_basis -= d.sss_ded
					if govt_type == 'phic':
						prev_government_basis += d.phic_inc
						prev_government_basis -= d.phic_ded
					if govt_type == 'hdmf':
						prev_government_basis += d.hdmf_inc
						prev_government_basis -= d.hdmf_ded

			if d.frequency != "5th":
				monthly_basis += d.government_basis

	test.append(_( ("{0}:{1}").format(curr_freq, current_basis ) ))
	#frappe.throw(_( test ))
	if govt_freq == "2nd":
		if no_weeks == "5" and curr_freq == "5th":
			government_basis = current_basis + prev_government_basis
		
		elif curr_freq == "4th" and no_weeks == "4":
			government_basis = current_basis + prev_government_basis


	elif govt_freq == "Both":
		if curr_freq == "2nd":
			government_basis = current_basis + prev_government_basis

		elif no_weeks == "4" and curr_freq == "4th":# or curr_freq == "5th":
			government_basis = current_basis + prev_government_basis

		elif no_weeks == "5" and curr_freq == "5th":
			government_basis = current_basis + prev_government_basis
	
	elif govt_freq == "All":
		freq_all_passed = 0
		if no_weeks in ["1", 1]:
			if curr_freq in ['1st']:
				freq_all_passed = 1
		if no_weeks in ["2", 2]:
			if curr_freq in ['1st', '2nd']:
				freq_all_passed = 1
		if no_weeks in ["3", 3]:
			if curr_freq in ['1st', '2nd', '3rd']:
				freq_all_passed = 1
		if no_weeks in ["4", 4]:
			if curr_freq in ['1st', '2nd', '3rd', '4th']:
				freq_all_passed = 1
		if no_weeks in ["5", 5]:
			if curr_freq in ['1st', '2nd', '3rd', '4th', '5th']:
				freq_all_passed = 1

		if freq_all_passed:
			government_basis = current_basis + prev_government_basis

	if monthly_basis:
		monthly_basis += current_basis

	#used for getting sss,phic,hdmf data an all previous frequencies
	weekly_previous_amts = {
		"sss": sss,
		"ssse": ssse,
		"sssc": sssc,
		"sss_ee_mpf": sss_ee_mpf,
		"sss_er_mpf": sss_er_mpf,
	}		

	return government_basis, monthly_basis, weekly_previous_amts

def get_weekly_targets(govt_freq, curr_freq, no_weeks):
	targets = []
	if govt_freq == "2nd":
		if no_weeks == "5":
			targets = ["1st","2nd","3rd","4th"]
		else:
			targets = ["1st","2nd","3rd"]

	elif govt_freq == "Both":
		if curr_freq == "2nd":
			targets = ["1st"]

		elif no_weeks == "4" and curr_freq == "4th":
			#targets = ["3rd"]
			targets = ["1st","2nd","3rd"]

		elif no_weeks == "5" and curr_freq == "5th":
			#targets = ["3rd","4th"]
			targets = ["1st","2nd","3rd","4th"]

	elif govt_freq == "All":
		#if curr_freq == "1st":
		#	targets = ["1st"]
		if curr_freq == "2nd":
			targets = ["1st"]
		if curr_freq == "3rd":
			targets = ["1st", "2nd"]
		if curr_freq == "4th":
			targets = ["1st", "2nd", "3rd"]
		if curr_freq == "5th":
			targets = ["1st", "2nd", "3rd", "4th"]

	return targets