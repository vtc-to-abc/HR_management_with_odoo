from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError, ValidationError
import datetime
from datetime import date,datetime, timedelta
from calendar import monthrange
from dateutil.relativedelta import relativedelta, MO

class ExtendContract(models.Model):
    _inherit = "hr.contract"
    _description = "Extend stuff"

    name = fields.Char(string='Tên Hợp Đồng', required=False)
    # employee_id = fields.Many2one('hr.employee', string='Nhan vien')

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
    @api.onchange('name')
    def test(self):
        print(self.state)
        print(self.name)
        print(self.employee_id.contract_id.name)
        print(self.contract_type)
    @api.model
    def update_state(self):
        """tim tat ca cac hop dong het han"""
        expired_contract_ids = self.search([
                                ('state', '=', 'open'),
                                '|',
                                ('date_end', '<=', fields.Date.to_string(date.today() + relativedelta(days=1))),
                                ])

        for contract in expired_contract_ids:
            next_contract = self.search([
                ('employee_id', '=', contract.employee_id.id),
                ('state', '=', 'daft'),
                ('date_start', '>', contract.date_start),
                ('date_start', '<=', fields.Date.to_string(date.today()))
            ], order="date_start desc", limit=1)
            contract.write({'state': 'close'})
            if next_contract:
                next_contract.write({'state': 'open'})

        """tu dong them moi hop dong hien tai neu khong co hop dong hien tai"""
        current_contracts = self.search([('state', '=', 'open')])
        for contract in current_contracts:
            if not contract:
                self.search([
                    ('employee_id', '=', contract.employee_id.id),
                    ('state', '=', 'daft'),
                    ('date_start', '<=', fields.Date.to_string(date.today()))
                ], order="date_start desc", limit=1).write({'state': 'open'})
        return True

    def _assign_open_contract(self):
        for contract in self:
            contract.employee_id.sudo().write({'contract_id': contract.id})

    def write(self, vals):
        res = super(ExtendContract, self).write(vals)
        if vals.get('state') == 'open':
            self._assign_open_contract()
        if vals.get('state') == 'close':
            for contract in self:
                contract.date_end = max(date.today(), contract.date_start)

        calendar = vals.get('resource_calendar_id')
        if calendar:
            self.filtered(lambda c: c.state == 'open' or (c.state == 'draft')).mapped('employee_id').write({'resource_calendar_id': calendar})

        return res

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
