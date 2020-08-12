# -*- coding: utf-8 -*-
# Copyright (c) 2020, OSI and contributors
# For license information, please see license.txt
from __future__ import unicode_literals
import frappe
from frappe.utils import cstr, add_days, date_diff
from frappe import _
from frappe.utils.csvutils import UnicodeWriter
from frappe.model.document import Document

class Convertrix(Document):
	pass

@frappe.whitelist()
def upload():

	settings = frappe.get_single('Convertrix')
	s_skip = int(settings.skipped_row)
	s_biometrics_id = int(settings.biometrics_id)-1
	s_card_type = int(settings.card_type)-1
	s_date_time = int(settings.date_time)-1
	s_device_id = int(settings.device_id)-1

	if not frappe.has_permission("Time Card", "create"):
		raise frappe.PermissionError

	from frappe.utils.csvutils import read_csv_content_from_uploaded_file
	from frappe.modules import scrub

	rows = read_csv_content_from_uploaded_file()
	rows = filter(lambda x: x and any(x), rows)
	if not rows:
		msg = [_("Please select a csv file")]
		return {"messages": msg, "error": msg}

	columns = []
	columns.extend(["biometrics_id","card_type","date","time","device_id"])

	ret = []
	error = False


	from frappe.utils.csvutils import check_record, import_doc

	for i, row in enumerate(rows[s_skip:]):
		if not row: continue
		row_idx = i + s_skip

		splited_row = row[0].split("\t")
		frow = [splited_row[s_biometrics_id],splited_row[s_card_type],splited_row[s_date_time].split(" ")[0],splited_row[s_date_time].split(" ")[1]+":00",splited_row[s_device_id]]

		d = frappe._dict(zip(columns, frow))
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
