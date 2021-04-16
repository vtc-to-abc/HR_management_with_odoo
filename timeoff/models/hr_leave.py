from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError, ValidationError
import datetime
from datetime import datetime, timedelta
from calendar import monthrange
from dateutil.relativedelta import relativedelta, MO
from odoo.tools import float_compare

class ExtendContract(models.Model):
    _inherit = "hr.leave"
    _description = "Extend stuff"

    employee_id = fields.Many2one(string="nhan vien")
    date_from = fields.Datetime(string='Ngay bat dau')
    date_to = fields.Datetime(string='Ngay het')
    number_of_days = fields.Float(string='So ngay xin')

    @api.constrains('state', 'number_of_days', 'holiday_status_id')
    def _check_holidays(self):
        mapped_days = self.mapped('holiday_status_id').get_employees_days(self.mapped('employee_id').ids)

        # p_time_off = so ngay nhan vien duoc ung phep theo loai hop dong
        p_time_off = float(str(self.employee_id.contract_id.contract_type[0]))
        for holiday in self:
            if holiday.holiday_type != 'employee' or not holiday.employee_id or holiday.holiday_status_id.allocation_type == 'no':
                continue
            leave_days = mapped_days[holiday.employee_id.id][holiday.holiday_status_id.id]

            # neu nhan vien co hop dong thi moi duoc phep xin nghi loai co allocation
            if p_time_off :
                """ xet so allocation con lai cua nhan vien. 
                        + Neu so allocation con lai >= 0 thi moi duoc phep xin nghi
                        + Neu so allocation con lai < 0 thi ko duoc phep xin nghi
                """
                if float_compare(leave_days['remanining_leaves'], 0, precision_digits=2) != -1:
                    if float_compare(leave_days['remaining_leaves'] + p_time_off, 0, precision_digits=2) == -1 or float_compare(leave_days['virtual_remaining_leaves'] + p_time_off, 0, precision_digits=2) == -1:
                        raise ValidationError(_('Khong duoc nghi qua so ngay cho phep'))
                else:
                    raise ValidationError(_("hien dang no phep, hay tra phep"))
            else:
                raise ValidationError(_('Chi nhan vien co hop dong moi duoc nghi cap phep'))