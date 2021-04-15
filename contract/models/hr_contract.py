from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError, ValidationError
import datetime
from datetime import datetime, timedelta
from calendar import monthrange
from dateutil.relativedelta import relativedelta, MO
class ExtendContract(models.Model):
    _inherit = "hr.contract"
    _description = "Extend stuff"

    name = fields.Char(string='Tên Hợp Đồng', required=False)
    employee_id = fields.Many2one('hr.employee', string='Nhan vien')

    contract_type = fields.Selection(selection=[('3ct', 'Chính thức'),
                                                ('2tv', 'Thử Việc')],
                                     string="Loại hợp đồng", default='2tv')

    date_start = fields.Date(string="Ngày bắt đầu HĐ", )
    date_end = fields.Date(string="Ngày kết thúc HĐ", readonly=True)
    contract_term = fields.Selection(string="Thời hạn HĐ",
                                     selection=[('1', '1 tháng'), ('3', '3 tháng'), ('6', '6 tháng'),
                                                ('12', '12 tháng'), ('24', '24 tháng'), ('36', '36 tháng'),],
                                     default='1')
    wage_form = fields.Char(string="Hình thức lương")
    state = fields.Selection(string="Trạng thái")

    @api.model
    def name_get(self):
        c_l = []
        for contract in self:
            name = contract.name
            if contract.contract_type:
                name = dict(contract._fields['contract_type'].selection).get(contract.contract_type)
            c_l.append([contract.id, name])
        return c_l

    @api.constrains("date_end")
    def _notification(self):
        if relativedelta(self.date_end, datetime.now()).years == 0 and relativedelta(self.date_end, datetime.now()).month == 0 and relativedelta(self.date_end, datetime.now()).days <= 3:
            raise ValidationError('test')

    @api.constrains("date_start", "contract_term")
    def _auto_end(self):
        f_c_t = 0
        print(self.contract_type)
        cur_year = int(self.date_start.year)
        cur_month = int(self.date_start.month)
        for x in range(1, int(self.contract_term)+1):
            if cur_month > 12:
                cur_year += 1
                cur_month = 1
            f_c_t += int(monthrange(cur_year, cur_month)[1])
            cur_month += 1

        e_d = self.date_start + timedelta(days=f_c_t)
        self.date_end = e_d
