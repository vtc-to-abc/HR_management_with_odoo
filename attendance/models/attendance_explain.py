import datetime

from odoo import models, fields, api, exceptions, _
from odoo.tools import format_datetime
from odoo.exceptions import UserError, ValidationError
import pytz

class AttendanceExplain(models.Model):
    _name = 'attendance.explain'
    _description = 'dsd'
    attendance_id = fields.Many2one('hr.attendance', string='Cham cong')
    off_explain_content = fields.Text(string='Noi dung giai trinh', required=True)

    @api.model
    def create(self, vals):
        result = super(AttendanceExplain, self).create(vals)
        # do what you want
        return result

