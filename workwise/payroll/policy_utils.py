from __future__ import unicode_literals
import frappe, datetime
from datetime import time, datetime
from frappe.utils import cint, flt, nowdate, add_days, getdate, fmt_money
from frappe import _

def get_policy(pname, company):
	pv = 0
	get_dafault = frappe.db.get_value("System Policy", pname, "default_value")
	if get_dafault:
		pv = get_dafault

	get_policy = frappe.db.sql("""SELECT SP.default_value, SPC.policy_value, SPC.filter_value FROM `tabSystem Policy` SP
		INNER JOIN `tabSystem Policy Companies` SPC WHERE SP.`name` = %s """,(pname), as_dict=1)

	for d in get_policy:
		if d.filter_value == company:
			pv = d.policy_value
		else:
			pv = get_dafault

	return pv

