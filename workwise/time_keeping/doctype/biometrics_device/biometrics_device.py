# -*- coding: utf-8 -*-
# Copyright (c) 2018, HDI Systech and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe, datetime, hashlib
from frappe.utils import cint, flt, nowdate, add_days, getdate, fmt_money, now_datetime, get_datetime, get_datetime_str
from zk import ZK, const
from frappe import _
from frappe.model.document import Document

class BiometricsDevice(Document):
	def get_connection(self):
		conn = ZK(self.device_ip, port=self.device_port, timeout=5, password=0, force_udp=False, ommit_ping=False)
		return conn

	def test_connection(self):
		conn = None
		zk = self.get_connection()
		try:
			conn = zk.connect()
			if conn:
				if self.check_sound:
					conn.test_voice(index=10)
				
				raise Exception('Connection Successfull')

		except Exception as e:
			frappe.msgprint(_('{}').format(e))
			self.create_log(_(" {0}, {1} ").format(self.device_ip, e))
			
		finally:
			if conn:
				conn.disconnect()

	def force_download(self):
		conn = None
		zk = ZK(self.device_ip, port=self.device_port, timeout=5, password=0, force_udp=False, ommit_ping=False)
		try:
			conn = zk.connect()
			if conn:
				attendances = conn.get_attendance()
				for d in attendances:
					log = str(d)
					log_user = (log.rsplit(": ", 1)[0]).replace(": ", "")
					log_datetime = (log.rsplit(": ", 1)[1]).replace(": ", "")
					log_date = (log.rsplit(": ", 1)[1]).replace(": ", "").rsplit(" ", 6)[0]
					log_time = (log.rsplit(": ", 1)[1]).replace(": ", "").rsplit(" ", 6)[1]
					log_type = ((log.rsplit(": ", 1)[1]).replace(": ", "").rsplit(" ", 1)[1]).replace(")", "")

					salt = hashlib.md5(str(log_user) + str(log_datetime))
					salt = salt.hexdigest()
					frappe.db.sql(""" INSERT IGNORE INTO `tabTime Card` ( `name`, creation, modified, modified_by, owner, docstatus, idx, card_type, `time`, `date`, biometrics_id, is_disabled) 
						VALUES ( '{0}', '{1}', '{2}', '{3}', '{4}', '{5}', '{6}', '{7}', '{8}', '{9}', '{10}', {11} )""".format( salt, now_datetime(), now_datetime(), 'Downloader', 'administrator', 
							0, 0, log_type, log_time, log_date, log_user, 0 ))

					frappe.db.commit()
					#frappe.msgprint(_(log_time))


		except Exception as e:
			frappe.msgprint(_('{}').format(e))
		
		finally:
			if conn:
				conn.disconnect()

	def create_log(self, log_return):
		bl = frappe.new_doc("Biometrics Log")
		bl.update({
			"device_name": self.name,
			"log_time": nowdate(),
			"log_return": log_return,
		})
		bl.insert()
