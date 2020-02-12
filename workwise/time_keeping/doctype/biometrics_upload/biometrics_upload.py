# -*- coding: utf-8 -*-
# Copyright (c) 2019, OSI and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.utils import cstr, add_days, date_diff
from frappe import _
from frappe.utils.csvutils import UnicodeWriter
from frappe.model.document import Document

class BiometricsUpload(Document):
	pass

@frappe.whitelist()
def get_template():
	if not frappe.has_permission("Time Card", "create"):
		raise frappe.PermissionError

	#args = frappe.local.form_dict
	w = UnicodeWriter()
	w = add_header(w)

	# write out response as a type csv
	frappe.response['result'] = cstr(w.getvalue())
	frappe.response['type'] = 'csv'
	frappe.response['doctype'] = "Biometrics Upload Template"

def add_header(w):
	w.writerow(["Notes:"])
	w.writerow(["Please do not change the template headings"])
	w.writerow(["Date should be in YYYY-MM-DD Format, Card Type Shoulde Be 0, 1, 2, 3, 4, 5"])
	w.writerow(["If you are overwriting existing attendance records, 'ID' column mandatory"])
	w.writerow(["Biometrics ID", "Card Type", "Date", "Time", "Location","Device ID"])
	return w

@frappe.whitelist()
def upload():
	if not frappe.has_permission("Time Card", "create"):
		raise frappe.PermissionError

	from frappe.utils.csvutils import read_csv_content_from_uploaded_file
	from frappe.modules import scrub

	rows = read_csv_content_from_uploaded_file()
	rows = filter(lambda x: x and any(x), rows)
	if not rows:
		msg = [_("Please select a csv file")]
		return {"messages": msg, "error": msg}
	columns = [scrub(f) for f in rows[4]]
	columns[0] = "biometrics_id"
	columns[1] = "card_type"
	columns[2] = "date"
	columns[3] = "time"
	columns[4] = "location"
	columns[5] = "device_id"
	ret = []
	error = False

	from frappe.utils.csvutils import check_record, import_doc

	for i, row in enumerate(rows[5:]):
		if not row: continue
		row_idx = i + 5
		d = frappe._dict(zip(columns, row))
		d["doctype"] = "Time Card"
		datesplit = d["date"].split('/')
		try:
			fdate = datesplit[2]+"-"+datesplit[0]+"-"+datesplit[1]
		except:
			fdate = d["date"]

		result = frappe.db.sql("""SELECT `name` FROM `tabTime Card` WHERE card_type = %s AND `date` = %s AND biometrics_id = %s AND `time` = %s LIMIT 1""",(d["card_type"],fdate,d["biometrics_id"],d["time"]),as_dict=True)
		for res in result:
			d["name"] = res.name
			
		try:
			check_record(d)
			ret.append(import_doc(d, "Time Card", 0 , row_idx, submit=False))
		except Exception, e:
			error = True
			ret.append('Error for row (#%d) %s : %s' % (row_idx,
				len(row)>1 and row[1] or "", cstr(e)))
			frappe.errprint(frappe.get_traceback())

	if error:
		frappe.db.rollback()
	else:
		frappe.db.commit()
	return {"messages": ret, "error": error}