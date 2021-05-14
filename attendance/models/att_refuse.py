import datetime

from odoo import models, fields, api, exceptions, _
from odoo.tools import format_datetime
from odoo.exceptions import UserError, ValidationError
import pytz

class AttendanceRefuse(models.Model):
    _name = 'attendance.refuse'
    _description = 'dsd1'
    attendance_id = fields.Many2one('hr.attendance', string='Cham cong')
    refuse_reasson = fields.Text(string='Ly do tu choi', required=True)

    def action_refuse_reasson(self):
        for record in self:
            record.attendance_id.action_off_explain(record.refuse_reasson)
            record.attendance_id.refuse_reasson = record.refuse_reasson
            record.attendance_id.state = 'refuse'



