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
        # expired_contract_ids = self.search([
        #     ('state', 'in', ['open']),
        #     ('date_end', '<=', fields.Date.to_string(date.today() + relativedelta(days=1))),
        # ])
        # for contract in expired_contract_ids:
        #     next_contract = self.search([
        #         ('employee_id', '=', contract.employee_id.id),
        #         ('state', 'in', ['draft']),
        #         ('date_start', '>', contract.date_start)
        #     ], order="date_start desc", limit=1)
        #     contract.write({'state': 'close'})
        #     if next_contract:
        #         next_contract.write({'state': 'open'})
        #     else:
        #         continue
        # closest_new_contracts = self.search([('state', 'in', ['draft'])], order="date_start desc")
        # print(closest_new_contracts)
        # for contract in closest_new_contracts:
        #     existed_current_contract = self.search([
        #             ('employee_id', '=', contract.employee_id.id),
        #             ('state', 'in', (['open'])),
        #             ])
        #     if not existed_current_contract:
        #         contract.write({'state': 'open'})
        print(self.id)
        print(self.state)
        print(self.name)
        print(self.employee_id.contract_id.name)
        print(self.contract_type)

    @api.model
    def update_state(self):
        # near_expire_contracts = self.search([
        #         ('state', '=', 'open'), ('kanban_state', 'in', ['blocked', 'done', 'normal']),
        #         '|',
        #         '&',
        #         ('date_end', '<=', fields.Date.to_string(date.today() + relativedelta(days=1))),
        #         ('date_end', '>=', fields.Date.to_string(date.today() + relativedelta(days=1))),
        #         '&',
        #         ('visa_expire', '<=', fields.Date.to_string(date.today() + relativedelta(days=60))),
        #         ('visa_expire', '>=', fields.Date.to_string(date.today() + relativedelta(days=1))),
        #     ])

        # for contract in near_expire_contracts:
        #     contract.activity_schedule(
        #         'mail.mail_activity_data_todo', contract.date_end,
        #         _("The contract of %s is about to expire.", contract.employee_id.name),
        #         user_id=contract.hr_responsible_id.id or self.env.uid)

        # near_expire_contracts.write({'kanban_state': 'blocked'})

        self.search([
            ('state', 'in', ['open']),
            '|',
            ('date_end', '<=', fields.Date.to_string(date.today() + relativedelta(days=1))),
            ('visa_expire', '<=', fields.Date.to_string(date.today() + relativedelta(days=1))),
        ]).write({'state': 'cancel'})

        expire_contract_ids = self.search(
                [('state', '=', 'cancel'), ('employee_id', '!=', False)], order="date_end desc")
        # Ensure all closed contract followed by a new contract have a end date.
        # If closed contract has no closed date, the work entries will be generated for an unlimited period.
        for contract in expire_contract_ids:
            existed_current_contract = self.search([
                               ('employee_id', '=', contract.employee_id.id),
                               ('state', 'in', (['open'])), ])
            if not existed_current_contract:
                next_contract = self.search([
                    ('employee_id', '=', contract.employee_id.id),
                    ('state', 'in', ['draft']),
                ], order="date_start desc", limit=1)
                if next_contract:
                    next_contract.write({'state': 'open'})
            else:
                continue

        closest_new_contracts = self.search([('state', 'in', ['draft'])], order="date_start desc")
        print(closest_new_contracts)
        for contract in closest_new_contracts:
             existed_current_contract = self.search([
                     ('employee_id', '=', contract.employee_id.id),
                     ('state', 'in', (['open'])),
                     ])
             if not existed_current_contract:
                 contract.write({'state': 'open'})

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
    def create(self, vals):
        contracts = super(ExtendContract, self).create(vals)
        if vals.get('state') == 'open':
            contracts._assign_open_contract()
        open_contracts = contracts.filtered(lambda c: c.state == 'open' or c.state == 'draft')
        # sync contract calendar -> calendar employee
        for contract in open_contracts.filtered(lambda c: c.employee_id and c.resource_calendar_id):
            contract.employee_id.resource_calendar_id = contract.resource_calendar_id
        return contracts

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

    @api.onchange("date_start", "contract_term")
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
