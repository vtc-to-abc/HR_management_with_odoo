from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError, ValidationError
from dateutil.relativedelta import relativedelta, MO
from datetime import datetime, timedelta
from calendar import monthrange

class ExtendEmployee(models.Model):
    _inherit = ["hr.employee"]
    _description = "Extend stuff"

    # base
    code = fields.Char(string="Mã Nhân Viên", required=False)
    department_id = fields.Many2one('hr.department', string="Bộ Phận", required=False)
    join_date = fields.Date(string="Ngày Tham gia", required=False)
    contract_ids = fields.One2many('hr.contract', 'employee_id', string='Danh sach hop dong cua empl')
    contract_id = fields.Many2one('hr.contract', string='Hợp Đồng Hiện Tại',
                                  groups="hr.group_hr_user", domain="[('company_id', '=', company_id)]",
                                  _rec_name='contract_type', store=True
                                  , help='Current contract of the employee',)

    job_title1 = fields.Selection(string='Vị trí làm việc',
                                 selection=[
                                     ('none', 'Chưa Sắp ep'),
                                     ('pm', 'PM'),
                                     ('ba', 'BA'),
                                     ('dev', 'Dev'),
                                     ('test', 'Test'),
                                     ('sale', 'Sales'),
                                     ('hr', 'HR'),
                                     ('des', 'Designer'),
                                 ], default='none')
    work_time = fields.Char(string="Thâm Niên", readonly=True, compute="_work_time_increase")
    parent_id = fields.Many2one('hr.employee', 'Người Quản Lý', compute="_compute_parent_id", store=False, readonly=False,
                                domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]")

    # work info
    job_position_lv = fields.Selection(string="Cấp Bậc",
                                       selection=[
                                           ('nv', 'Nhân viên'),
                                           ('tn', 'Trưởng Nhóm'),
                                           ('gd', 'Giám Đốc'),
                                           ('ceo', 'CEO')
                                       ], default="nv")
    work_status = fields.Selection(string="TT làm việc",
                                   selection=[
                                       ('not onboard', 'Không onboad'),
                                       ('working', 'Đang làm việc'),
                                       ('long vacation', 'Nghỉ dài hạn'),
                                       ('off', 'Đã nghỉ việc')
                                   ], default='working')
    off_date = fields.Date(string="Ngày Thôi Việc", requried=False)
    # thuc ra la many2one. Nhung hien tai la selection
    office = fields.Selection(string="Địa Điểm Làm Việc",
                              selection=[
                                  ('pb1', 'PB1'),
                                  ('pb2', 'PB2'),
                                  ('pb3', 'PB3'),
                                  ('pb4', 'PB4'),
                              ], default="pb1")
    salary_rate = fields.Float(string="Bậc Lương", default=1.0)
    off_main_reason = fields.Selection(string='Lý do thôi việc',
                                        selection=[
                                            ('ld1', 'Lương và chế độ đãi ngộ'),
                                            ('ld2', 'Điều kiện và môi trường làm việc'),
                                            ('ld3', 'Sếp và đồng nghiệp'),
                                            ('ld4', 'Văn hóa công ty')
                                        ], default='ld1')
    off_detail_reason = fields.Text(string='Chi tiết lý do thôi việc')
    # contact info
    phone = fields.Char(string="Điện thoại")
    private_email = fields.Char(string="Email cá nhân")
    skype_id = fields.Char(string="Skype", required=False)
    facebook_link = fields.Char(string="Facebook", required=False)
    emergency_phone = fields.Char(string="Điện thoại người thân")
    relative_name = fields.Char(string="Tên người thân")

    # private info
    identification_id = fields.Char(string="CMT/CCCD")
    identification_issued_date = fields.Date(string="Ngày Cấp", required=False)
    identification_issued_place = fields.Char(string="Nơi Cấp", required=False)
    identification_old = fields.Char(string="ID cũ", requried=False)
    tax_code = fields.Char(string="Mã số thuế", required=False)
    bank_name = fields.Char(string="Tên ngân hàng", required=False)
    bank_account = fields.Char(string="Số tài khoản")
    bank_branch = fields.Char(string="Chi nhánh", required=False)

    gender = fields.Selection(string="Giới Tính",
                              selection=[
                                  ('male', 'Nam'),
                                  ('female', 'Nữ'),
                                  ('other', 'Khác'),
                              ], default='other')
    birthday = fields.Date(string="Ngày sinh")

    country_of_birth = fields.Many2one('res.country', string="Quê quán",goups="hr.group_hr_user", tracking=True)
    place_of_birth = fields.Char(string="Nơi sinh")
    resident_address = fields.Char(string="Đ/c thường trú")
    staying_address = fields.Char(string="Đ/c tạm trú")
    marital = fields.Selection(string="TT hôn nhân",
                               selection=[
                                   ('s', 'Độc thân'),
                                   ('m', 'Đã kết hôn'),
                               ], default="s")

    bank_account_id = fields.Many2one(
        'res.partner.bank', 'Bank Account Number',
        domain="[('partner_id', '=', address_home_id), '|', ('company_id', '=', False), ('company_id', '=', company_id)]",
        groups="hr.group_hr_user",
        tracking=True,
        help='Employee bank salary account')
    # resume
    # provide
    gsuite_provided = fields.Selection(string="Cấp G-suite",
                                    selection=[
                                        ('no', 'Không'),
                                        ('done', 'Đã Cấp'),
                                        ('wait', 'Chờ Cấp')
                                    ], default="no")
    gsuite_account = fields.Char(string="Tài Khoản G-suite")
    gsuite_pwd = fields.Char(string="Mật khẩu")
    device_provided = fields.Selection(string="Cấp thiết bị",
                                    selection=[
                                        ('no', 'Không'),
                                        ('done', 'Đã Cấp'),
                                        ('wait', 'Chờ Cấp')
                                    ], default="no")
    device = fields.Selection(string="Thiết bị",
                              selection=[
                                  ('t1', 'Tag 1'),
                                  ('t2', 'Tag 2'),
                                  ('t3', 'Tag 2')
                              ], default="t1"
                              )
    parking_ticket_provided = fields.Selection(string="Cấp thẻ gửi xe",
                                    selection=[
                                        ('no', 'Không'),
                                        ('done', 'Đã Cấp'),
                                        ('wait', 'Chờ Cấp')
                                    ], default="no")
    VIN = fields.Char(string="Biển số xe")
    vehicle_type = fields.Char(string="Loại xe")

    # contract

    # profile
    profile_status = fields.Selection(string="TT Hồ sơ",
                                    selection=[
                                        ('no', 'Chưa nộp'),
                                        ('yes', 'Đã nộp'),
                                    ], default="no")
    profile_handed = fields.Char(string="Hồ sơ đã nộp")
    expire_date = fields.Date(string="Ngày hết hạn nộp")
    day_til_expire = fields.Integer(string="Só ngày đến hạn")

    # setting
    user_id = fields.Many2one('res.users', string='TK người dùng', related='resource_id.user_id', store=True, readonly=False)
    pin = fields.Char(string="Mã chấm công")
    leave_manager_id = fields.Many2one(
        'res.users', string='Người duyệt nghỉ phép',
        compute='_compute_leave_manager', store=True, readonly=False,
        help='Select the user responsible for approving "Time Off" of this employee.\n'
             'If empty, the approval is done by an Administrator or Approver (determined in settings/users).')
    other_certificate = fields.Char(string="Other Certificate", required=False)

    @api.depends('join_date')
    def _work_time_increase(self):
        w_y = str(relativedelta(datetime.now(), self.join_date).years)
        w_m = str(relativedelta(datetime.now(), self.join_date).months)
        w_d = str(relativedelta(datetime.now(), self.join_date).days)

        self.work_time = ("%s năm %s tháng %s ngày" % (w_y, w_m, w_d))

    @api.constrains('name')
    def _check_name(self):

        for record in self:
            if record['name'].isupper():
                print(record['name'])
                raise ValidationError("this is suckkkkkkkkkk")

    # timeoff allocation
    allocation_count = fields.Float(string='Số ngày phép được cấp.')
    allocation_used_count = fields.Float(string='Số ngày phép được cấp da dung')


