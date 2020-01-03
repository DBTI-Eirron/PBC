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
	ret = []
	error = False

	from frappe.utils.csvutils import check_record, import_doc

	for i, row in enumerate(rows[5:]):
		if not row: continue
		row_idx = i + 5
		d = frappe._dict(zip(columns, row))
		d["doctype"] = "Time Card"

		if d.name:
			d["docstatus"] = frappe.db.get_value("Time Card", d.name, "docstatus")
		try:
			check_record(d)
			ret.append(import_doc(d, "Time Card", 1, row_idx, submit=False))
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