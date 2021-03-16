from __future__ import unicode_literals
import frappe, datetime
from frappe import _
from frappe.model.document import Document
from frappe.utils import cint, flt, getdate, cstr, add_to_date

def get_rates(emp):
	monthly_rate = 0.0
	hourly_rate = 0.0
	semi_rate = 0.0
	daily_rate = 0.0
	weekly_rate = 0.0
	if emp['rate'] > 0 and  emp['total_yr_days'] > 0 and emp['no_hours'] > 0:
		month_days = (flt(emp['total_yr_days'], 8) / 12)
		if emp['rate_type'] == "Monthly Rate":
			monthly_rate = flt(emp['rate'], 8)
			semi_rate = flt(emp['rate'], 8) / 2
			daily_rate = flt(emp['rate'], 8) / month_days
			hourly_rate = ( flt(emp['rate'], 8) / month_days ) / emp['no_hours']
			weekly_rate = (flt(emp['rate'], 8) / month_days) * 7

		elif emp['rate_type'] == "Hourly Rate":
			monthly_rate = ( flt(emp['rate'], 8) * emp['no_hours'] ) * month_days
			semi_rate = ( flt(emp['rate'], 8) * emp['no_hours'] ) * (month_days / 2)
			daily_rate = flt(emp['rate'], 8) * emp['no_hours']
			hourly_rate = flt(emp['rate'], 8)
			weekly_rate = ( flt(emp['rate'], 8) * emp['no_hours'] ) * 7

		elif emp['rate_type'] == "Daily Rate":
			monthly_rate = flt(emp['rate'], 8) * month_days
			semi_rate = flt(emp['rate'], 8) * (month_days / 2)
			daily_rate = flt(emp['rate'], 8)
			hourly_rate = flt(emp['rate'], 8) / emp['no_hours']
			weekly_rate = flt(emp['rate'], 8) * 7
		
		elif emp['rate_type'] == "Weekly Rate":
			monthly_rate = (flt(emp['rate'], 8) / 7) * month_days
			semi_rate = (flt(emp['rate'], 8) / 7) * (month_days / 2)
			daily_rate = flt(emp['rate'], 8) / 7
			hourly_rate = (flt(emp['rate'], 8) / 7) / emp['no_hours']
			weekly_rate = flt(emp['rate'], 8)

	return {
		"monthly_rate": monthly_rate,
		"semi_rate": semi_rate,
		"daily_rate": daily_rate,
		"hourly_rate": flt(hourly_rate, 8),
		"weekly_rate": flt(weekly_rate, 8)
	}

def get_overtime_map():
	ot_map = {}
	ot = frappe.db.sql(""" SELECT ot_code, ot_rate, daily_ot_rate, transaction_type FROM `tabOvertime Rates` """, as_dict=1)
	for t in ot:
		ot_map[t.ot_code] = {
			"rate": t.ot_rate,
			"daily_rate": t.daily_ot_rate,
			"transaction_type": t.transaction_type,
		}
	return ot_map

def get_transaction_map():
	tr_map = {}
	tr = frappe.db.sql("""SELECT code, title, type, entry_type, account, is_taxable, 
		is_bonus, is_sss, is_phic, is_hdmf, is_standard, is_active, bir_type FROM `tabTransaction Type` """, as_dict=1)
	for t in tr:
		tr_map[t.code] = {"code": t.code, "title": t.title, "type": t.type, "bir_type": t.bir_type, "entry_type": t.entry_type,	"account": t.account, 
			"is_taxable": t.is_taxable, "is_standard": t.is_standard, "is_active": t.is_active, "is_bonus": t.is_bonus, "is_government": t.is_government,
			"is_sss": t.is_sss, "is_phic": t.is_phic, "is_hdmf": t.is_hdmf,
		}

	return tr_map

def get_location_map():
	loc_map = {}
	loc = frappe.db.sql("""SELECT `name`, company, min_wage FROM `tabLocation` """, as_dict=1)
	for l in loc:
		loc_map[l.name] = { "name": l.name, "company": l.company, "min_wage": l.min_wage }

	return loc_map

def get_adjustment_settings():
	settings = {
		"inc_ab": "", "inc_uho": "", "inc_ot": "", "inc_nd": "", "inc_lt": "", "inc_ut": "",
		"ded_ab": "", "ded_uho": "", "ded_ot": "", "ded_nd": "", "ded_lt": "", "ded_ut": "",
	}

	inc_ab = frappe.db.get_single_value('Payroll Settings', 'def_adj_inc_ab')
	inc_uho = frappe.db.get_single_value('Payroll Settings', 'def_adj_inc_uho')
	inc_ot = frappe.db.get_single_value('Payroll Settings', 'def_adj_inc_ot')
	inc_nd = frappe.db.get_single_value('Payroll Settings', 'def_adj_inc_nd')
	inc_lt = frappe.db.get_single_value('Payroll Settings', 'def_adj_inc_lt')
	inc_ut = frappe.db.get_single_value('Payroll Settings', 'def_adj_inc_ut')
	inc_cto = frappe.db.get_single_value('Payroll Settings', 'def_adj_inc_cto')

	ded_ab = frappe.db.get_single_value('Payroll Settings', 'def_adj_ded_ab')
	ded_uho = frappe.db.get_single_value('Payroll Settings', 'def_adj_ded_uho')
	ded_ot = frappe.db.get_single_value('Payroll Settings', 'def_adj_ded_ot')
	ded_nd = frappe.db.get_single_value('Payroll Settings', 'def_adj_ded_nd')
	ded_lt = frappe.db.get_single_value('Payroll Settings', 'def_adj_ded_lt')
	ded_ut = frappe.db.get_single_value('Payroll Settings', 'def_adj_ded_ut')
	ded_cto = frappe.db.get_single_value('Payroll Settings', 'def_adj_ded_cto')

	settings.update({
		"inc_ab": inc_ab, "inc_uho": inc_uho, "inc_ot": inc_ot, "inc_nd": inc_nd, "inc_lt": inc_lt, "inc_ut": inc_ut, "inc_cto": inc_cto,
		"ded_ab": ded_ab, "ded_uho": ded_uho, "ded_ot": ded_ot, "ded_nd": ded_nd, "ded_lt": ded_lt, "ded_ut": ded_ut, "ded_cto": ded_cto,
	})

	return settings

def get_sss_table():
	sss_table = frappe.db.sql(""" SELECT beginning, ending, employee, employer, ec, mpf_ee, mpf_er FROM `tabSSS Table` """, as_dict=True )
	return sss_table

def get_sss_amount(amount, sss_table):
	sss, ssse, sssc, sss_ee_mpf, sss_er_mpf = 0, 0, 0, 0, 0
	for d in list(filter(lambda x: x['beginning'] <= amount <= x['ending'], sss_table)):
		sss, ssse, sssc, sss_ee_mpf, sss_er_mpf = d.employee, d.employer, d.ec, d.mpf_ee, d.mpf_er

	return sss, ssse, sssc, sss_ee_mpf, sss_er_mpf

def get_hdmf_table():
	sss_table = frappe.db.sql(""" SELECT beginning, ending, employee, employer FROM `tabHDMF Table` """, as_dict=True )
	return sss_table

def get_hdmf_amount(amount, hdmf_table):
	hdmf, hdmfe = 0, 0
	for d in list(filter(lambda x: x['beginning'] <= amount <= x['ending'], hdmf_table)):
		hdmf, hdmfe = d.employee, d.employer
	return hdmf, hdmfe

def update_transaction_accounts():
	#bench execute workwise.payroll.payroll_utils.update_transaction_accounts
	transaction_types = frappe.db.sql(""" SELECT `name`, debit_acct, credit_acct, debit_account, credit_account FROM `tabTransaction Type` """, as_dict=True )
	period_groups = frappe.db.sql(""" SELECT `name` FROM `tabPeriod Group` """, as_dict=True)
	groups = []

	for pg in period_groups:
		groups.append(pg.name)

	for tt in transaction_types:
		tr = frappe.get_doc('Transaction Type', tt.name)
		existing = []

		for acct in tr.get('accounts'):
			existing.append(acct.get('period_group'))

		for gr in groups:
			if gr not in existing:
				if tt.get('debit_acct') or tt.get('credit_account'):
					tr.append("accounts", {
						"period_group": gr,
						"debit_account": tt.get('debit_acct'),
						"debit_code": tt.get('debit_account'),	
						"credit_account": tt.get('credit_acct'),
						"credit_code": tt.get('credit_account'),
					})

		tr.flags.ignore_permissions = True
		tr.save()

def sssc_fix():
	#bench execute workwise.payroll.payroll_utils.sssc_fix
	fixes = frappe.db.sql(""" SELECT * FROM `SSSCFIX` """, as_dict=True )
	for d in fixes:
		fix = frappe.get_doc('Payroll Register', d.register_id)
		pr_types = []
		for pre in fix.get('payroll_register_entries'):
			pr_types.append(pre.get('pay_code'))

		if "SSSC" not in pr_types:
			fix.append("payroll_register_entries", {
				"pay_type": "None",
				"pay_code": "SSSC",
				"pay_description": "SSS Compensation",	
				"entry_type": "Compensation",
				"amount": d.change_to,
				"cost_center": d.cost_center,
				"is_taxable": 1,
				"is_bonus": 0,
			})
		elif "SSSC" in pr_types:
			for rf in fix.get('payroll_register_entries'):
				if rf.get('pay_code') == "SSSC":
					setattr(rf, 'amount', d.change_to)

		fix.flags.ignore_permissions = True
		fix.save()


def update_multi_ot_trans(): 
	#bench execute workwise.payroll.payroll_utils.update_multi_ot_trans
	frappe.db.sql("""UPDATE `tabOvertime Rates` SET transaction_type = 'OT' """)
	frappe.db.sql("""UPDATE `tabTransaction Type` SET entry_type = 'Overtime' WHERE `name` = 'OT' """)

def update_daily_ot_rate(): 
	#bench execute workwise.payroll.payroll_utils.update_daily_ot_rate
	#Set Daily OT Rate Default equalt to OT Rate
	frappe.db.sql("""UPDATE `tabOvertime Rates` SET daily_ot_rate = ot_rate """)

def format_decimal_by_2(figure):
	return '{:,.2f}'.format( flt(figure, 2) )

def format_decimal_by_2_align_right(figure):
	return '<div align="right">'+str( '{:,.2f}'.format( flt(figure, 2) ) )+'</div>'

def format_decimal_by_2_align_right_negative(figure):
	return '<div align="right">('+str( '{:,.2f}'.format( flt(abs(figure), 2) ) )+')</div>'

def format_precision(figure, precision):
	if precision == '2':
		return '{:,.2f}'.format( flt(figure, 2) )
	elif precision == '3':
		return '{:,.3f}'.format( flt(figure, 3) )
	elif precision == '4':
		return '{:,.4f}'.format( flt(figure, 4) )
	elif precision == '5':
		return '{:,.5f}'.format( flt(figure, 5) )
	elif precision == '6':
		return '{:,.6f}'.format( flt(figure, 6) )
	elif precision == '7':
		return '{:,.7f}'.format( flt(figure, 7) )
	else:
		return '{:,.8f}'.format( flt(figure, 8) )

def format_align_right(figure):
	return '<div align="right">'+str( figure )+'</div>'

def get_ot_class_map():
	ot_class_map = {}
	ot = frappe.db.sql(""" SELECT OTR.`name`, OTR.`transaction_type`, OTR.`ot_code`, OTR.`ot_rate`, OTR.`daily_ot_rate`, ORC.`rate_class`, ORC.`rate_type`,ORC.`rate` 
		FROM `tabOvertime Rates` OTR INNER JOIN `tabOT Rate Class` ORC ON OTR.`name` = ORC.parent """, as_dict=1)
	for t in ot:
		if t.ot_code not in ot_class_map:
			ot_class_map[t.ot_code] = {}
		if t.rate_class not in ot_class_map[t.ot_code]:
			ot_class_map[t.ot_code][t.rate_class]= {}
		ot_class_map[t.ot_code][t.rate_class][t.rate_type] = {
			"rate": t.rate,
			"transaction_type": t.transaction_type if t.transaction_type else "OT",
		}
	return ot_class_map
def get_rateclass_map():
	rateclass_map = {}
	rateclass = frappe.db.sql(""" SELECT * FROM `tabRate Classification` """, as_dict=1)
	otrateclass = frappe.db.sql(""" SELECT * FROM `tabOT Rate Class` """, as_dict=1)

	for rc in rateclass:
		rateclass_map[rc.name] = {
			"early_nd": rc.early_nd,
			"lt_nd": rc.lt_nd,
			"otrate_class": [],
		}

	for ot in otrateclass:
		if ot.rate_class in rateclass_map:
			rateclass_map[rc.name]['otrate_class'].append({
				"rate_type": ot.rate_type,
				"rate": ot.rate,
			})

	return rateclass_map

def get_company_map():
	co_map = {}
	co = frappe.db.sql(""" SELECT name, tax_id, sss_id, phic_id, hdmf_id, rdo_code FROM `tabCompany` """, as_dict=1)
	for c in co:
		co_map[c.name] = {
			"company_name": c.name,
			"tax_id": c.tax_id,
			"sss_id": c.sss_id,
			"phic_id": c.phic_id,
			"hdmf_id": c.hdmf_id,
			"rdo_code": c.rdo_code
		}

	return co_map