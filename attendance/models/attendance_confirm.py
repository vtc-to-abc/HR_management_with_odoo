import datetime

from odoo import models, fields, api, exceptions, _
from odoo.tools import format_datetime
from odoo.exceptions import UserError, ValidationError
import pytz

class AttendanceConfirm(models.Model):
    _name = "attendance.confirm"
    _description = "Extend Attendance"