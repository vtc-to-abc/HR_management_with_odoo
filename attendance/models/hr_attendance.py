import datetime

from odoo import models, fields, api, exceptions, _
from odoo.tools import format_datetime
from odoo.exceptions import UserError, ValidationError
import pytz


class CustomAttendance(models.Model):
    _inherit = "hr.attendance"
    _description = "Extend Attendance"
    _order = "check_in desc"

    attendant_code = fields.Char(string='Mã chấm công')
    working_time = fields.Selection(selection=[
                                    ('weekend', 'Cuoi tuan'),
                                    ('holiday', 'Nghi le'),
                                    ('workday', 'Ngay lam viec')],
                                    string='Thời gian làm việc',
                                    store=True,
                                    compute='_auto_working_time')

    leave_status_in_day = fields.Selection(selection=[
                                            ('NS', 'Nghỉ sáng'),
                                            ('NC', 'Nghi chieu'),
                                            ('CN', 'Ca Ngay'),
                                            ('K', 'Khong')],
                                            string='Trang thai xin nghi',
                                            store=True,
                                            compute='_check_leave_status')

    pay_type = fields.Selection(selection=[
                                ('paid', 'Nghi co luong'),
                                ('unpaid', 'Nghi khong luong')],
                                string="loai chi tra",)

    # note: xay ra sau khi da xin nghi va da hoan thanh check out.
    off_explain_need = fields.Char(string="Can giai trinh", store=True, compute='_work_day_and_off_explain')

    # note: moi nhan vien can phai co giai trinh ve ngay cong cua minh
    # va de ngay cong cua nhan vien co gia tri, thi giai trinh do phai duoc manager phe duyet
    work_day = fields.Float(string='Ngay cong', default=0.0, store=True, compute='_work_day_and_off_explain')

    workday_confirm = fields.Selection(selection=[
                                        ('NN', 'Nua Ngay'),
                                        ('CN', 'Ca Ngay'), ],
                                        default='',
                                        string='Giai trinh cham cong')

    number_late = fields.Integer(string='Trang thai di muon', store=True, compute='_check_late')
    late_confirm = fields.Selection(selection=[
                                    ('muon', 'Di Muon'),
                                    ('ko', 'Khong Di Muon'),
                                    ('phep', 'Muon Co Phep')],
                                    default='',
                                    string='Giai trinh di muon')

    state = fields.Selection(selection=[
                            ('wait', 'Cho phe duyet'),
                            ('explain', 'Can giai trinh'),
                            ('approved', 'Da phe duyet'),
                            ('refuse', 'Tu choi'),
                            ('draft', 'Nhap')],
                            store=True,
                            compute="_auto_state",
                            string='Trang thai giai trinh',)

    off_explain = fields.One2many('attendance.explain', 'attendance_id')
    off_explain_content = fields.Text(string='Noi dung giai trinh')
    refuse_reasson = fields.Text(string='Ly do tu choi')
    check_in = fields.Datetime(string='Gio vao')
    check_out = fields.Datetime(string='Gia ra')
    worked_hours = fields.Float(string='Gio lam viec')

    @api.depends('late_confirm')
    def _check_late(self):
        for record in self:
            if record.late_confirm in ['ko', 'phep']:
                record.number_late = 0
            elif record.late_confirm == 'muon':
                record.number_late = 1

    @api.constrains('workday_confirm')
    def wd_confirm(self):
        if self.leave_status_in_day in ['NS', 'NC'] and self.workday_confirm == 'CN':
            raise ValidationError("Nhan vien da nghi sang hoac chieu")

    def action_off_explain(self):
        if not self.off_explain:
            explain = self.env['attendance.explain'].create({'attendance_id': self.id, 'off_explain_content': ' '})
            self.env.cr.commit()

        self.off_explain_content = self.off_explain.off_explain_content

        return {
            'name': 'Giai Trinh',
            'context': "{'edit': True}",
            'res_model': 'attendance.explain',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_id':  int(self.off_explain.id),
            'views_id': 'custom_view_attendance_explain',
            #'attendance_id': int(self.id),
            'target': 'new'}

    def action_approve(self):
        #view_ref = self.env['ir.ui.view'].get_object_reference('hr.attendance', 'view_approval_popup_from')
        return {
            'name': 'Phe Duyet',
            'context': "{'edit': True}",
            'res_model': 'hr.attendance',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_id': int(self.id),
            'views_id': 'view_approval_popup_from',
            'target': 'new'}

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
        print(self.off_explain)
        time_format = "%Y-%m-%d %H:%M:%S"
        for record in self:
            local_check_in = datetime.datetime.strptime(record.check_in.astimezone(pytz.timezone('Asia/Ho_Chi_Minh'))
                    .strftime(time_format), time_format)

            emp_time_off = self.env['hr.leave'].search([('date_from', '<=', local_check_in),
                                                        ('date_to', '>=', local_check_in),
                                                        ('employee_id.id', '=', record.employee_id.id), ])
            emp_half_time_off = self.env['hr.leave'].search([('request_date_from', '=', local_check_in),
                                                        ('employee_id.id', '=', record.employee_id.id), ])

            if not emp_time_off and not emp_half_time_off:
                print('no time off')
                record.leave_status_in_day = 'K'

            if emp_time_off.state in ['draft', 'confirm']:
                print('in draft')
                record.leave_status_in_day = 'K'

            if emp_half_time_off.state in ['draft', 'confirm']:
                record.leave_status_in_day = 'K'

            if emp_time_off.state in ['validate', 'validate1'] and not emp_time_off.request_unit_half:
                record.leave_status_in_day = 'CN'

            if emp_half_time_off.state in ['validate', 'validate1'] and emp_half_time_off.request_unit_half:

                if emp_half_time_off.request_date_from_period == 'pm':
                    record.leave_status_in_day = 'NC'
                elif emp_half_time_off.request_date_from_period == 'am':
                    record.leave_status_in_day = 'NS'

    @api.depends('check_in', 'check_out', 'working_time', 'workday_confirm')
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

            # đề phòng lỗi lệch timezone
            time_format = "%Y-%m-%d %H:%M:%S"
            local_check_in = datetime.datetime.strptime(record.check_in.astimezone(pytz.timezone('Asia/Ho_Chi_Minh'))
                                                        .strftime(time_format), time_format)

            """ trường ngày công - [work_day] và trường giải trình - [off_explain_need] 
                chỉ nhận giá trị khi nhân viên đã check out
            """
            if record.check_out:
                local_check_out = datetime.datetime.strptime(record.check_out.astimezone(pytz.timezone('Asia/Ho_Chi_Minh'))
                                                         .strftime(time_format), time_format)

                if record.workday_confirm == 'NN':
                    record.work_day = 0.5
                elif record.workday_confirm == 'CN':
                    record.work_day = 1.0
                # nếu tình trạng nghỉ của nhân là cả ngày, thì không cần giải trình lý do
                if record.leave_status_in_day == 'CN':
                    record.off_explain_need = 'Khong'
                else:
                    # tính ngày công:

                    # nếu sáng đến muộn quá hạn, chiều về sớm => ko tính công
                    if local_check_out < noon_end and local_check_in > morning_begin_end\
                            and not record.workday_confirm:
                        print('wd 0')
                        record.work_day = 0.0

                    # neu chiều đến muộn quá hạn, chiều về muộn => ko tính công???
                    if local_check_in > noon_begin_end and local_check_out > noon_end\
                            and not record.workday_confirm:
                        print('wd 1')
                        record.work_day = 0.

                    # tạm thời chưa tính ngày công vào cuối tuần hoặc nghỉ lễ
                    if record.working_time != 'workday'\
                            and not record.workday_confirm:
                        record.work_day = 0.0

                    # nếu sáng đến trước hạn, chiều về sớm => tính nửa ngày công
                    if local_check_out < noon_end and local_check_in < morning_begin_end\
                            and not record.workday_confirm:
                        print('wd 2')
                        record.work_day = 0.5

                    # nếu sáng đến muộn quá hạn (hoặc nghỉ sáng) nhưng chiều đến sớm. và chiều về muộn => tính nửa ngày công
                    if local_check_out > noon_end and morning_begin_end <= local_check_in < noon_begin_end\
                            and not record.workday_confirm:
                        print('wd 3')
                        record.work_day = 0.5

                    # nếu sáng đến trước hạn và chiều về đúng quy định => tính cả ngày công
                    if local_check_in < morning_begin_end and local_check_out >= noon_end\
                            and not record.workday_confirm:
                        print('wd 4')
                        record.work_day = 1.0

                    # những trường hợp nghỉ sau không cần phải giải trình:
                    """" nếu sáng đến sớm trước quy định (< 8h35), chiều về muộn hoặc đúng so với quy định(>= 17h35).
                    và không xin nghỉ vào ngày đó.
                    """
                    if local_check_in < morning_begin_start and local_check_out >= noon_end \
                            and record.leave_status_in_day == 'K':
                        record.off_explain_need = 'Khong'

                    """nếu sáng đến sớm nhưng chiều về sớm. Và có xin nghỉ vào buổi chiều"""
                    if local_check_in < morning_begin_start and local_check_out < noon_end \
                        and record.leave_status_in_day == 'NC':
                        record.off_explain_need = 'Khong'

                    """ nếu chiều đến sớm, về đúng. Và có xin nghỉ buổi sáng"""
                    if local_check_in < noon_begin_start and local_check_out > noon_end \
                        and record.leave_status_in_day == 'NS':
                        record.off_explain_need = 'Khong'

                    # những trường hợp nghỉ sau được coi là về sớm, cần giải trình:
                    """nếu sáng đến sớm, chiều về sớm. Nhưng không có xin nghỉ"""
                    if local_check_in < morning_begin_start and local_check_out < noon_end \
                        and record.leave_status_in_day == 'K':
                        record.off_explain_need = 'Ve Som'

                    """ nếu sáng đến sớm và về sớm. Nhưng lại xin nghỉ vào buổi chiều"""
                    if local_check_in < morning_begin_start and local_check_out < morning_end \
                        and record.leave_status_in_day == 'NC':
                        record.off_explain_need = 'Ve Som'

                    """nếu chiều đến muộn, nhưng không xin nghỉ vào buổi chiều"""
                    if local_check_in > noon_begin_start and record.leave_status_in_day != 'NC':
                        record.off_explain_need = 'Ve Som'

                    # những trường hợp nghỉ sau được coi là M836 hoặc M836, về sớm và cần được giải trình:

                    """nếu sáng đến trong khoảng muộn cho phép. Và xin nghỉ chiều hoặc không xin  nghỉ=> M836"""
                    if morning_begin_start < local_check_in < morning_begin_end \
                        and record.leave_status_in_day in ['NC', 'K']:
                        record.off_explain_need = 'M836'

                    """nếu sáng đến trong khoảng muộn cho phép, nhưng chiều về sớm. Và không xin nghỉ => M836, ve som"""
                    if morning_begin_start < local_check_in < morning_begin_end and local_check_out < noon_end \
                        and record.leave_status_in_day == 'K':
                        record.off_explain_need = 'M836, Ve Som'

                    """nếu sáng đến trong khoảng muộn cho phép, nhưng sáng về sớm. 
                    Và đã xin nghỉ  chiều=> M836, ve som"""
                    if morning_begin_start < local_check_in < morning_begin_end and local_check_out < morning_end \
                        and record.leave_status_in_day == 'NC':
                        record.off_explain_need = 'M836, Ve Som'

                    # những trường hợp nghỉ sau được coi là M931 hoặc M931, về sớm:
                    """nếu sáng đến muộn hoặc nghỉ sáng và chiều đến trước hạn. 
                    Đồng thời không xin nghỉ hoặc có xin nghỉ buổi chiều => M931"""
                    if morning_begin_end < local_check_in < noon_begin_end \
                        and record.leave_status_in_day  in ['K', 'NC']:
                        record.off_explain_need = 'M931'

                    """ nếu sáng đến muộn hoặc nghỉ sáng và chiều đến trước hạn.
                    Đồng thời không xin nghỉ => M931, về sớm"""
                    if morning_begin_end < local_check_in < noon_begin_start and local_check_out < noon_end \
                        and record.leave_status_in_day == 'K':
                        record.off_explain_need = 'M931, Ve Som'

                    """nếu sáng đến muộn và về sớm. Đồng thời đã xin nghỉ chiều => M931, về sớm"""
                    if morning_begin_end < local_check_in and local_check_out < morning_end \
                        and record.leave_status_in_day == 'NC':
                        record.off_explain_need = 'M931, Ve Som'

                    # những trường hợp nghỉ sau đuwọc coi là M1306 hoặc M1406, về sớm
                    """nếu chiều đến trong khoảng muộn cho phép và đã xin nghỉ sáng hoặc hoặc không xin nghỉ"""
                    if noon_begin_start < local_check_in < noon_begin_end \
                        and record.leave_status_in_day in ['K', 'NS']:
                        record.off_explain_need = 'M1306'

                    """nếu chiều đến trong khoảng muộn cho phép nhưng lại về sớm.
                    Đồng thời đã xin nghỉ sáng hoặc không xin => M1306. về sớm"""
                    if noon_begin_start < local_check_in < noon_begin_end  and local_check_out < noon_end\
                        and record.leave_status_in_day in ['K', 'NS']:
                        record.off_explain_need = 'M1306, Ve Som'

                    # các trường hợp dưới đây được coi là M1431 hoặc M1431, về sớm:
                    """nếu chiều đến muộn mà đã xin nghỉ sáng hoặc không xin nghỉ => M1431"""
                    if noon_begin_end < local_check_in <= day_end and record.leave_status_in_day in ['K', 'NS']:
                        record.off_explain_need = 'M1431'

                    """nếu chiều đến muôn và về sớm> Mà đx xin nghỉ sáng hoặc không xin nghỉ => M1431, về sớm"""
                    if noon_begin_end < local_check_in <= day_end and local_check_out < noon_end \
                        and record.leave_status_in_day in ['K', 'NS']:
                        record.off_explain_need = 'M1431, Ve Som'

    @api.depends('off_explain_need')
    def _check_late(self):
        for record in self:
            if record.off_explain_need in ['M836', 'M1306', 'M836, Ve Som', 'M1306, Ve Som']:
                record.number_late = 1
            elif record.off_explain_need in ['M931', 'M1431', 'M931, Ve Som', 'M1431, Ve Som']:
                record.number_late = 0

    @api.depends('off_explain_need', 'off_explain')
    def _auto_state(self):
        for record in self:
            if record.off_explain_need == 'Khong':
                record.state = False
            if record.off_explain_need != 'Khong':
                record.state = 'explain'
                if record.off_explain_content and record.state != 'approved' and record.state != 'refuse':
                    record.state = 'wait'


