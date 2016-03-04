#This file is part of Tryton.  The COPYRIGHT file at the top level of
#this repository contains the full copyright notices and license terms.
from decimal import Decimal
from trytond.model import ModelView, ModelSQL, fields
from trytond.wizard import Wizard, StateView, StateAction, StateTransition, \
    Button
from trytond.report import Report
from trytond.pyson import Eval, PYSONEncoder, Date
from trytond.transaction import Transaction
from trytond.pool import Pool

__all__ = ['OpenTotalVoucher', 'OpenTotal', 'TotalVoucher']

class OpenTotalVoucher(ModelView):
    'Open Total Voucher'
    __name__ = 'nodux_electronic_invoice_auth.print_total_voucher.start'
    fiscalyear = fields.Many2One('account.fiscalyear', 'Fiscal Year',
        required=True)
    start_period = fields.Many2One('account.period', 'Start Period',
        domain=[
            ('fiscalyear', '=', Eval('fiscalyear')),
            ('start_date', '<=', (Eval('end_period'), 'start_date'))
            ],
        depends=['end_period', 'fiscalyear'])
    end_period = fields.Many2One('account.period', 'End Period',
        domain=[
            ('fiscalyear', '=', Eval('fiscalyear')),
            ('start_date', '>=', (Eval('start_period'), 'start_date')),
            ],
        depends=['start_period', 'fiscalyear'])
    company = fields.Many2One('company.company', 'Company', required=True)
    
    @staticmethod
    def default_fiscalyear():
        FiscalYear = Pool().get('account.fiscalyear')
        return FiscalYear.find(
            Transaction().context.get('company'), exception=False)

    @staticmethod
    def default_company():
        return Transaction().context.get('company')

    @fields.depends('fiscalyear')
    def on_change_fiscalyear(self):
        return {
            'start_period': None,
            'end_period': None,
            }
            
class OpenTotal(Wizard):
    'Open Total'
    __name__ = 'nodux_electronic_invoice_auth.print_total'
    
    start = StateView('nodux_electronic_invoice_auth.print_total_voucher.start',
        'nodux_electronic_invoice_auth.print_total_voucher_start_view_form', [
            Button('Cancel', 'end', 'tryton-cancel'),
            Button('Print', 'print_', 'tryton-ok', default=True),
            ])
    print_ = StateAction('nodux_electronic_invoice_auth.report_total_voucher')
    
    def do_print_(self, action):
        if self.start.start_period:
            start_period = self.start.start_period.id
        else:
            start_period = None
        if self.start.end_period:
            end_period = self.start.end_period.id
        else:
            end_period = None
        data = {
            'company': self.start.company.id,
            'fiscalyear': self.start.fiscalyear.id,
            'start_period': start_period,
            'end_period': end_period,
            }
        return action, data

    def transition_print_(self):
        return 'end'

class TotalVoucher(Report):
    'Total Voucher Issued'
    __name__ = 'nodux_electronic_invoice_auth.total_voucher'
    
    @classmethod
    def parse(cls, report, objects, data, localcontext):
        pool = Pool()
        print "ingresa al metodo"
        Invoice = pool.get('account.invoice')
        Company = pool.get('company.company')
        company = Company(data['company'])
        invoice = Invoice.search([('type','=', 'out_invoice'),('state','=', 'posted')])
        credit = Invoice.search([('type','=', 'out_credit_note'),('state','=', 'posted')])
        withholding = Invoice.search([('type','=', 'in_withholding'),('state','=', 'posted')])
        debit = Invoice.search([('type','=', 'out_debit_note'),('state','=', 'posted')])
        shipment = Invoice.search([('type','=', 'out_shipment'),('state','=', 'posted')])
        number_invoice = 0
        number_credit = 0
        number_debit = 0
        number_withholding = 0
        number_shipment = 0
        value_1 = 0.08 
        value_2 =0.06
        value_3 =0.04
        value_4 =0.03
        
        if Invoice:
            for i in invoice:
                number_invoice = number_invoice +1
            for c in credit:
                number_credit = number_credit +1
            for w in withholding:
                number_withholding = number_withholding +1
            for d in debit:
                number_debit = number_debit +1
            for s in shipment:
                number_shipment = number_shipment +1
        total_voucher= number_invoice + number_credit +number_withholding+number_debit + number_shipment
        if number_invoice < 1001:
            value_invoice = number_invoice * value_1
        elif number_invoice < 10001:
            value_invoice = number_invoice * value_2
        elif number_invoice < 50001:
            value_invoice = number_invoice * value_3
        elif number_invoice > 50001:
            value_invoice = number_invoice * value_4
        
        
        return str(number_invoice)
        return str(number_credit)
        return str(number_debit)
        return str(number_withholding)
        return str(number_shipment)
        
        localcontext['company'] = company
        localcontext['contador_invoice'] = number_invoice
        localcontext['contador_credit'] = number_credit
        localcontext['contador_debit'] = number_debit
        localcontext['contador_withholding'] = number_witholding
        localcontext['contador_shipment'] = number_shipment
        localcontext['total_voucher'] = total_voucher
         
        return super(TotalVoucher, cls).parse(report, objects, data, 
            localcontext)
