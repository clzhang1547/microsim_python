class Leave:
    def __init__(self, leave_type, length):
        self.leave_type = leave_type
        self.length = length
        self.leave_num = 0
        self.need_num = 0
        self.length_prog_year = 0
        self.unifrom_draw_leave_length = 0
        self.days_benefits = 0
        self.days_paid = 0
        self.days_unpaid = 0
        self.days_benefits_prog_year = 0
        self.days_paid_prog_year = 0
        self.days_unpaid_prog_year = 0
        self.begin = None
        self.end = None
        self.begin_prog_year = None
        self.end_prog_year = None
        self.truncated = False
        self.paid = False
        self.benefits = False
        self.full_paid = False
        self.weekly_wage = 0
        self.leave_weeks = 0
        self.pay_amt = 0
        self.pay_amt_prog_year = 0
        self.pay_amt_no_prog = 0
        self.benefits_amt = 0
        self.benefits_amt_prog_year = 0
        self.lost_product = 0
        self.uncompensated_amt = 0
        self.pay_amt_no_prog_prog_year = 0
        self.lost_product_prog_year = 0
        self.uncompensated_amt_prog_year = 0

        self.w_pay = []
        self.w_pay_prog_year = []
        self.days_pay = []
        self.days_pay_prog_year = []
        self.w_benefits = []
        self.w_benefits_prog_year = []
        self.days_ben = []
        self.days_ben_prog_year = []

        self.doctor = False
        self.hospital = False
        self.eligible = False
        self.leave_taken_back = False
        self.reason_taken_back = 0

        self.need = False
        self.length_no_prog = 0
        self.length_no_prog_prog_year = 0
        self.end_no_prog = None
        self.end_no_prog_prog_year = None

        self.w_pay_no_prog = []
        self.days_pay_no_prog = []
        self.w_pay_induced = []
        self.w_pay_no_prog_prog_year = []
        self.days_pay_no_prog_prog_year = []
        self.w_pay_induced_prog_year = []
