from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError, ValidationError
import datetime
from datetime import datetime, timedelta
from calendar import monthrange
from dateutil.relativedelta import relativedelta, MO

class ExtendContract(models.Model):
    _inherit = "hr.leave"
    _description = "Extend stuff"

    employee_id = fields.Many2one(string="nhan vien")
    date_from = fields.Datetime(string='Ngay bat dau')
    date_to = fields.Datetime(string='Ngay het')
    number_of_days = fields.Float(string='So ngay xin')


    @api.depends('date_from', 'date_to', 'employee_id')
    def _compute_number_of_days(self):
        for holiday in self:
            if holiday.date_from and holiday.date_to:
                holiday.number_of_days = \
                holiday._get_number_of_days(holiday.date_from, holiday.date_to, holiday.employee_id.id)['days']
            else:
                holiday.number_of_days = 0

    @api.constrains('state', 'number_of_days', 'holiday_status_id')
    def _check_holidays(self):

        allocated_count = self.employee_id.allocation_count

        allocated_used = self.employee_id.allocation_used_count
        #print(allocated_left)
        e_cur_contract = self.employee_id.contract_id.contract_type[0]
        p_time_off = int(str(self.employee_id.contract_id.contract_type[0]))
        #self.env['hr.contract'].search([('id', '=', '%s' % e_cur_contract)], limit=1).contract_type)[0])

        print( p_time_off)
        if p_time_off > 0:
            if self.number_of_days - (allocated_count - allocated_used) > p_time_off:
                raise ValidationError('ko duoc nghi qua ung phep')
        else:
            raise ValidationError('ko co hop dong')
