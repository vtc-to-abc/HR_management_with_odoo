import datetime

from odoo import models, fields, api, exceptions, _
from odoo.tools import format_datetime
import pytz

class CustomAttendance(models.Model):
    _inherit = "hr.attendance"
    _description = "Extend Attendance"
    _order = "check_in desc"

    attendant_code = fields.Char(string='Mã chấm công')
    working_time = fields.Selection(string='Thời gian làm việc',
                                    selection=[('weekend','Cuoi tuan'), ('holiday','Nghi le'),
                                                                         ('workday','Ngay lam viec')],
                                    store=True,
                                    compute='_auto_working_time')

    leave_status_in_day = fields.Selection(string='Trang thai xin nghi', selection=[('NS', 'Nghỉ sáng'), ('NC', 'Nghi chieu'),
                                                                    ('CN', 'Ca Ngay'), ('K', 'Khong')],
                                           store=True, compute='_check_leave_status')
    pay_type = fields.Selection(string="loai chi tra", selection=[('paid', 'Nghi co luong'), ('unpaid', 'Nghi khong luong')])

    # xay ra sau khi da xin nghi va da hoan thanh check out.
    off_explain_need = fields.Char(string="Can giai trinh", store=True, compute='_work_day_and_off_explain')

    work_day = fields.Float(string='Ngay cong', default=0.0, store=True, compute='_work_day_and_off_explain')
    late_count = fields.Integer(string='So lan di muon')
    off_explain_content = fields.Text(string='Noi dung giai trinh')
    approve_status = fields.Selection(string='Trang thai phe duyet',
                                          selection=[('request', 'Xin phe duyet'), ('explain', 'Can giai trinh'),
                                                     ('approved', 'Da phe duyet'), ('Decline', 'Tu choi'), ('draft', 'Nhap')])
    decline_reasson = fields.Text(string='Ly do tu choi')

    check_in = fields.Datetime(string='Gio vao')
    check_out = fields.Datetime(string='Gia ra')
    worked_hours = fields.Float(string='Gio lam viec')

    @api.depends('check_in')
    def _auto_working_time(self):
        time_format = "%Y-%m-%d"

        for record in self:
            local_check_in = datetime.datetime.strptime(
                record.check_in.astimezone(pytz.timezone('Asia/Ho_Chi_Minh'))
                .strftime(time_format), time_format)

            if local_check_in.weekday() in [5, 6]:
                record.working_time = 'weekend'
            else:
                record.working_time = 'workday'

    @api.depends('employee_id', 'check_in')
    def _check_leave_status(self):
        time_format = "%Y-%m-%d %H:%M:%S"
        for record in self:
            if record.working_time == 'workday':
                local_check_in = datetime.datetime.strptime(record.check_in.astimezone(pytz.timezone('Asia/Ho_Chi_Minh'))
                        .strftime(time_format), time_format)

                """ leave_status = 'K' khi nhan vien do khong co khoang tg nghi trong time off 
                trung vs ngay check_in"""
                emp_time_off = self.env['hr.leave'].search([('date_from', '<=', local_check_in),
                                                            ('date_to', '>=', local_check_in),
                                                            ('employee_id.id', '=', record.employee_id.id),])
                if not emp_time_off:
                    print('no time off')
                    record.leave_status_in_day = 'K'

                """ leave_status = 'K' khi nhan vien do co khoang tg nghi trong time off trung vs ngay check_in
                nhung yeu cau time off do van chua duoc duyet (trang thai cua yeu cau time off la draft hoac confirm)"""
                emp_time_off_not_approved = self.env['hr.leave'].search([('date_from', '<=', local_check_in),
                                                                   ('date_to', '>=', local_check_in),
                                                                   ('employee_id.id', '=', record.employee_id.id),
                                                                    ('state', 'in', ['draft', 'confirm']),
                                                                    ])
                if emp_time_off_not_approved:
                    print('in draft')
                    record.leave_status_in_day = 'K'

                """leave_status = 'CN' neu nhan vien do co tg nghi time off da duoc duyet, 
                vs truong [request_unit_half] =False, trung voi ngay check in
                """
                emp_full_time_off_approved = self.env['hr.leave'].search([('date_from', '<=', local_check_in),
                                                                   ('date_to', '>=', local_check_in),
                                                                   ('employee_id.id', '=', record.employee_id.id),
                                                                    ('state', 'in', ['validate', 'validate1']),
                                                                    ('request_unit_half', '=', False),])
                if emp_full_time_off_approved:
                    record.leave_status_in_day = 'CN'

                """leave_status = NC neu nhan vien co tg nghi time off, da duoc duyet va [request_unit_half]=true 
                + [request_date_from period] = pm, trung voi ngay check in
                """
                emp_noon_time_off_approved = self.env['hr.leave'].search([('request_date_from', '=', local_check_in),
                                                                          ('employee_id.id', '=', record.employee_id.id),
                                                                          ('state', 'in', ['validate', 'validate1']),
                                                                          ('request_unit_half', '=', True),
                                                                          ('request_date_from_period', '=', 'pm'),])
                if emp_noon_time_off_approved:
                    record.leave_status_in_day = 'NC'

                """leave_status = NS, neu co tg nghi trong time off, da duoc duyet + [request_half_day]=True
                + [request_date_from_period] = 'am', trung voi ngay check_in
                """
                emp_morning_time_off_approved = self.env['hr.leave'].search([('request_date_from', '=', local_check_in),
                                                                            ('employee_id.id', '=', record.employee_id.id),
                                                                            ('state', 'in', ['validate', 'validate1']),
                                                                            ('request_unit_half', '=', True),
                                                                            ('request_date_from_period', '=', 'am'),])
                if emp_morning_time_off_approved:
                    record.leave_status_in_day = 'NS'

    @api.depends('check_in', 'check_out', 'working_time')
    def _work_day_and_off_explain(self):
        daycheck = datetime.datetime.now()
        for record in self:

            morning_begin_start = daycheck.replace(year=record.check_in.year, month=record.check_in.month,
                                                   day=record.check_in.day, hour=8, minute=35, second=0)
            morning_begin_end = daycheck.replace(year=record.check_in.year, month=record.check_in.month,
                                                 day=record.check_in.day, hour=9, minute=30, second=0)
            morning_end = daycheck.replace(year=record.check_in.year, month=record.check_in.month,
                                           day=record.check_in.day, hour=12, minute=0, second=0)
            noon_begin_start = daycheck.replace(year=record.check_in.year, month=record.check_in.month,
                                                day=record.check_in.day, hour=13, minute=5, second=0)
            noon_begin_end = daycheck.replace(year=record.check_in.year, month=record.check_in.month,
                                              day=record.check_in.day, hour=14, minute=30, second=0)
            noon_end = daycheck.replace(year=record.check_in.year, month=record.check_in.month,
                                        day=record.check_in.day, hour=17, minute=30, second=0)
            day_end = daycheck.replace(year=record.check_in.year, month=record.check_in.month,
                                       day=record.check_in.day, hour=23, minute=59, second=0)
            # de phong loi lech
            time_format = "%Y-%m-%d %H:%M:%S"

            local_check_in = datetime.datetime.strptime(record.check_in.astimezone(pytz.timezone('Asia/Ho_Chi_Minh'))
                                                        .strftime(time_format), time_format)
            if record.check_out:
                local_check_out = datetime.datetime.strptime(record.check_out.astimezone(pytz.timezone('Asia/Ho_Chi_Minh'))
                                                         .strftime(time_format), time_format)
                if record.working_time == 'workday':
                    if record.leave_status_in_day == 'CN':
                        record.off_explain_need = 'Khong'
                    else:
                        if local_check_out < noon_end and local_check_in > morning_begin_end:
                            print('wd 0')
                            record.work_day = 0.0
                            if local_check_in < noon_begin_start and record.leave_status_in_day != 'NS':
                                record.off_explain_need = 'M931, Ve Som'

                        if local_check_in > noon_begin_end and local_check_out > noon_end:
                            print('wd 1')
                            record.work_day = 0.0

                        if local_check_out < noon_end and local_check_in < morning_begin_end:
                            print('wd 2')
                            record.work_day = 0.5
                            if local_check_in < morning_begin_start:
                                if record.leave_status_in_day == 'K':
                                    record.off_explain_need = 'Ve Som'
                                elif local_check_out < morning_end and record.leave_status_in_day == 'NC':
                                    record.off_explain_need = 'Ve Som'
                                elif local_check_out >= morning_end and record.leave_status_in_day == 'NC':
                                    record.off_explain_need = 'Khong'

                        if local_check_out > noon_end and morning_begin_end <= local_check_in < noon_begin_end:
                            print('wd 3')
                            record.work_day = 0.5
                            if local_check_in < noon_begin_start and record.leave_status_in_day == 'NS':
                                record.off_explain_need = 'Khong'
                            if record.leave_status_in_day != 'NC':
                                record.off_explain_need = 'M931'

                        if noon_begin_start < local_check_in and record.leave_status_in_day != 'NC':
                            record.off_explain_need = 'M1306'
                            if local_check_out < noon_end:
                                record.off_explain_need = 'M1306, Ve Som'
                                if record.leave_status_in_day == 'NS':
                                    record.off_explain_need = 'Ve Som'

                        if local_check_in < morning_begin_end and local_check_out >= noon_end:
                            print('wd 4')
                            record.work_day = 1.0
                            if local_check_in < morning_begin_start and record.leave_status_in_day == 'K':
                                record.off_explain_need = 'Khong'

                            elif morning_begin_start < local_check_in and record.leave_status_in_day != 'NS':
                                record.off_explain_need = 'M836'
                                if local_check_out < noon_end:
                                    record.off_explain_need = 'M836, Ve Som'

                        if noon_begin_end < local_check_in <= day_end and record.leave_status_in_day != 'NC':
                            record.off_explain_need = 'M1431'
                            if local_check_out < noon_end:
                                record.off_explain_need = 'M1431, Ve Som'

                else:
                    record.work_day = 0

