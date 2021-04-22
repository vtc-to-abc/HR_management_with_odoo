from odoo import api, fields, models
from odoo.exceptions import ValidationError
class CusHolidaysType(models.Model):
    _inherit = "hr.leave.allocation"
    _description = "Custom Time Off Type"

    contract_id = fields.Many2one(
        'hr.contract', compute='_compute_from_holiday_type', store=True, string='Loai hop dong', index=True, readonly=False, ondelete="restrict", tracking=True,
        states={'cancel': [('readonly', True)], 'refuse': [('readonly', True)],
                'validate1': [('readonly', True)], 'validate': [('readonly', True)]})
    contract_type = fields.Selection(string='Loai hop dong', selection=[('3ct', 'Chinh thuc'),
                                                                        ('2tv', 'Thu viec'),])

    holiday_type = fields.Selection(
        selection=[('employee', 'By Employee'),
        ('company', 'By Company'),
        ('department', 'By Department'),
        ('category', 'By Employee Tag'),
        ('contract', 'loai hop dong')]
        ,ondelete='CASCADE')

    @api.depends('holiday_type')
    def _compute_from_holiday_type(self):
        for allocation in self:
            if allocation.holiday_type == 'contract':
                allocation.employee_id = False
                allocation.mode_company_id = False

    def _action_validate_create_childs(self):
        childs = self.env['hr.leave.allocation']
        if self.state == 'validate' and self.holiday_type in ['category', 'department', 'company', 'contract']:
            if self.holiday_type == 'category':
                employees = self.category_id.employee_ids
            elif self.holiday_type == 'department':
                employees = self.department_id.member_ids
                print(employees)
            elif self.holiday_type == 'contract':
                employees = self.env['hr.employee'].search([('contract_id.contract_type', '=', self.contract_type)])
                for e in employees:
                    print(e.name)
            else:
                employees = self.env['hr.employee'].search([('company_id', '=', self.mode_company_id.id)])

            for employee in employees:
                childs += self.with_context(
                    mail_notify_force_send=False,
                    mail_activity_automation_skip=True
                ).create(self._prepare_holiday_values(employee))
            # TODO is it necessary to interleave the calls?
            childs.action_approve()
            if childs and self.validation_type == 'both':
                childs.action_validate()
        return childs
