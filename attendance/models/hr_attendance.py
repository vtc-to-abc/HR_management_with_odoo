import datetime

from odoo import models, fields, api, exceptions, _
from odoo.tools import format_datetime
import pytz

class CustomAttendance(models.Model):
    _inherit = "hr.attendance"
    _description = "Extend Attendance"
    _order = "check_in desc"

    attendant_code = fields.Char(string='Mã chấm công')
    working_time = fields.Selection(selection=[
                                    ('weekend','Cuoi tuan'),
                                    ('holiday','Nghi le'),
                                    ('workday','Ngay lam viec')],
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

    # xay ra sau khi da xin nghi va da hoan thanh check out.
    off_explain_need = fields.Char(string="Can giai trinh", store=True, compute='_work_day_and_off_explain')

    work_day = fields.Float(string='Ngay cong', default=0.0, store=True, compute='_work_day_and_off_explain')
    late_count = fields.Integer(string='So lan di muon')
    off_explain_content = fields.Text(string='Noi dung giai trinh')
    approve_status = fields.Selection(selection=[
                                        ('request', 'Xin phe duyet'),
                                        ('explain', 'Can giai trinh'),
                                        ('approved', 'Da phe duyet'),
                                        ('Decline', 'Tu choi'),
                                        ('draft', 'Nhap')],
                                        string='Trang thai phe duyet',)

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
            local_check_in = datetime.datetime.strptime(record.check_in.astimezone(pytz.timezone('Asia/Ho_Chi_Minh'))
                    .strftime(time_format), time_format)

            emp_time_off = self.env['hr.leave'].search([('date_from', '<=', local_check_in),
                                                        ('date_to', '>=', local_check_in),
                                                        ('employee_id.id', '=', record.employee_id.id), ])

            """ leave_status = 'K' khi nhan vien do khong co khoang tg nghi trong time off 
            trung vs ngay check_in"""
            if not emp_time_off:
                    print('no time off')
                    record.leave_status_in_day = 'K'

            """ leave_status = 'K' khi nhan vien do co khoang tg nghi trong time off trung vs ngay check_in
            nhung yeu cau time off do van chua duoc duyet (trang thai cua yeu cau time off la draft hoac confirm)"""
            if emp_time_off.state in ['draft', 'confirm']:
                print('in draft')
                record.leave_status_in_day = 'K'

            """leave_status = 'CN' neu nhan vien do co tg nghi time off da duoc duyet, 
                vs truong [request_unit_half] =False, trung voi ngay check in
            """
            if emp_time_off.state == 'validate1' and not emp_time_off.request_unit_half:
                record.leave_status_in_day = 'CN'

            """Xet truong hop nghi nua ngay, neu nhan vien co tg nghi time off, da duoc duyet, [request_unit_half] = true
            trung voi ngay check in"""
            if emp_time_off.state in ['validate', 'validate1'] and emp_time_off.request_unit_half:
                """leave_status = NC, neu [request_date_from period] = pm.
                Nguoc lai leave_status = NS, neu [request_date_from_period] = am
                """
                if emp_time_off.request_date_from_period == 'pm':
                    record.leave_status_in_day = 'NC'
                elif emp_time_off.request_date_from_period == 'am':
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

                # nếu tình trạng nghỉ của nhân là cả ngày, thì không cần giải trình lý do
                if record.leave_status_in_day == 'CN':
                    record.off_explain_need = 'Khong'
                else:
                    # tính ngày công:

                    # nếu sáng đến muộn, chiều về sớm => ko tính công
                    if local_check_out < noon_end and local_check_in > morning_begin_end:
                        print('wd 0')
                        record.work_day = 0.0

                    # neu chiều đến muộn, chiều về muộn => ko tính công???
                    if local_check_in > noon_begin_end and local_check_out > noon_end:
                        print('wd 1')
                        record.work_day = 0.

                    # tạm thời chưa tính ngày công vào cuối tuần hoặc nghỉ lễ
                    if record.working_time != 'workday':
                        record.work_day = 0.0

                    # nếu sáng đến sớm, chiều về sớm => tính nửa ngày công
                    if local_check_out < noon_end and local_check_in < morning_begin_end:
                        print('wd 2')
                        record.work_day = 0.5

                    # nếu sáng đến muộn(hoặc nghỉ sáng) nhưng chiều đến sớm. và chiều về muộn => tính nửa ngày công
                    if local_check_out > noon_end and morning_begin_end <= local_check_in < noon_begin_end:
                        print('wd 3')
                        record.work_day = 0.5

                    # nếu sáng đến sớm và chiều về đúng quy định => tính cả ngày công
                    if local_check_in < morning_begin_end and local_check_out >= noon_end:
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
