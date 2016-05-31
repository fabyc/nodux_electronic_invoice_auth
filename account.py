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
import base64
import psycopg2
import xmlrpclib

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
        
    party = fields.Many2One('party.party', 'Party')
    
    @staticmethod
    def default_fiscalyear():
        FiscalYear = Pool().get('account.fiscalyear')
        return FiscalYear.find(
            Transaction().context.get('company'), exception=False)

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
            
        if self.start.party:
            start_party = self.start.party.id
        else:
            start_party = None
        data = {
            'party': start_party,
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
        Period = pool.get('account.period')
        Fiscal = pool.get('account.fiscalyear')
        Party = pool.get('party.party')
        party = Party(data['party'])
        fiscal = Fiscal(data['fiscalyear'])
        start = Period(data['start_period'])
        end = Period(data['end_period'])
        fiscal_start = fiscal.start_date
        fiscal_end = fiscal.end_date
        if start.id != None:
            start_p_start = start.start_date
            end_p_start = (start.end_date)
        else: 
            start_p_start = None
            end_p_start = None
            
        if end.id != None:
            start_p_end = (end.start_date)
            end_p_end = (end.end_date)
        else:
            start_p_end = None
            end_p_end = None
            
        if party.id != None:
            number = party.vat_number
            value_1 = party.value_1
            value_2 = party.value_2
            value_3 = party.value_3
            value_4 = party.value_1
        else:
            number = None
            value_1 = 0.08 
            value_2 =0.06
            value_3 =0.04
            value_4 =0.03
            
        conn = psycopg2.connect("dbname=usuarios_web")
        cur = conn.cursor()
        cont = 0
        cont_c = 0
        cont_d = 0
        cont_w = 0
        cont_s = 0
        
        if start_p_start != None:
            if start_p_end != None:
                if number != None:
                    cur.execute("SELECT * FROM factura_web WHERE ruc = %s AND tipo ='out_invoice'", (number,))
                    result_invoice = cur.fetchall()
                    
                    cur.execute("SELECT * FROM factura_web WHERE ruc = %s AND tipo ='out_credit_note'", (number,))
                    result_credit = cur.fetchall()
                    
                    cur.execute("SELECT * FROM factura_web WHERE ruc = %s AND tipo ='out_debit_note'", (number,))
                    result_debit = cur.fetchall()
                    
                    cur.execute("SELECT * FROM factura_web WHERE ruc = %s AND tipo ='in_withholding'", (number,))
                    result_withholding = cur.fetchall()
                    
                    if result_invoice:
                        for r in result_invoice:
                            if (r[4] >= str(start_p_start)) and (r[4] <= str(end_p_end)):
                                 cont = cont +1 
                                 print "fechas ", r[4], str(start_p_start), str(end_p_end)
                    
                    if result_credit:
                        for r in result_credit:
                            if (r[4] >= str(start_p_start)) and (r[4] <= str(end_p_end)):
                                 cont_c = cont_c +1 
                                 print "fechas ", r[4], str(start_p_start), str(end_p_end)
                    
                    if result_debit:
                        for r in result_debit:
                            if (r[4] >= str(start_p_start)) and (r[4] <= str(end_p_end)):
                                 cont_d = cont_d +1 
                                 print "fechas ",r[4], str(start_p_start), str(end_p_end)
                    
                    if result_withholding:
                        for r in result_withholding:
                            if (r[4] >= str(start_p_start)) and (r[4]<= str(end_p_end)):
                                 cont_w = cont_w +1 
                                 print "fechas ", r[4], str(start_p_start), str(end_p_end)
                
                else: 
                    cur.execute("SELECT * FROM factura_web WHERE tipo ='out_invoice'")
                    result_invoice = cur.fetchall()
                    
                    cur.execute("SELECT * FROM factura_web WHERE tipo ='out_credit_note'")
                    result_credit = cur.fetchall()
                    
                    cur.execute("SELECT * FROM factura_web WHERE tipo ='out_debit_note'")
                    result_debit = cur.fetchall()
                    
                    cur.execute("SELECT * FROM factura_web WHERE tipo ='in_withholding'")
                    result_withholding = cur.fetchall()
                    
                    if result_invoice:
                        for r in result_invoice:
                            if (r[4] >= str(start_p_start)) and (r[4] <= str(end_p_start)):
                                 cont = cont +1 
                    
                    if result_credit:
                        for r in result_credit:
                            if (r[4] >= str(start_p_start)) and (r[4] <= str(end_p_start)):
                                 cont_c = cont_c +1 
                    
                    if result_debit:
                        for r in result_debit:
                            if (r[4] >= str(start_p_start)) and (r[4] <= str(end_p_start)):
                                 cont_d = cont_d +1 
                    
                    if result_withholding:
                        for r in result_withholding:
                            if (r[4] >= str(start_p_start)) and (r[4]<= str(end_p_start)):
                                 cont_w = cont_w +1 
            else:
                if number != None:
                    cur.execute("SELECT * FROM factura_web WHERE ruc = %s AND tipo ='out_invoice'", (number,))
                    result_invoice = cur.fetchall()
                    
                    cur.execute("SELECT * FROM factura_web WHERE ruc = %s AND tipo ='out_credit_note'", (number,))
                    result_credit = cur.fetchall()
                    
                    cur.execute("SELECT * FROM factura_web WHERE ruc = %s AND tipo ='out_debit_note'", (number,))
                    result_debit = cur.fetchall()
                    
                    cur.execute("SELECT * FROM factura_web WHERE ruc = %s AND tipo ='in_withholding'", (number,))
                    result_withholding = cur.fetchall()
                    
                    if result_invoice:
                        for r in result_invoice:
                            if (r[4] <= str(start_p_start)) and (r[4] <= str(end_p_start)):
                                 cont = cont +1 

                    if result_credit:
                        for r in result_credit:
                            if (r[4] >= str(start_p_start)) and (r[4] <= str(end_p_start)):
                                 cont_c = cont_c +1 
                    
                    if result_debit:
                        for r in result_debit:
                            if (r[4] >= str(start_p_start)) and (r[4] <= str(end_p_start)):
                                 cont_d = cont_d +1 
                    
                    if result_withholding:
                        for r in result_withholding:
                            if (r[4] >= str(start_p_start)) and (r[4]<= str(end_p_start)):
                                 cont_w = cont_w +1 
                
                else: 
                    cur.execute("SELECT * FROM factura_web WHERE tipo ='out_invoice'")
                    result_invoice = cur.fetchall()
                    
                    cur.execute("SELECT * FROM factura_web WHERE tipo ='out_credit_note'")
                    result_credit = cur.fetchall()
                    
                    cur.execute("SELECT * FROM factura_web WHERE tipo ='out_debit_note'")
                    result_debit = cur.fetchall()
                    
                    cur.execute("SELECT * FROM factura_web WHERE tipo ='in_withholding'")
                    result_withholding = cur.fetchall()
                    
                    if result_invoice:
                        for r in result_invoice:
                            if (r[4] >= str(start_p_start)) and (r[4] <= str(end_p_start)):
                                 cont = cont +1 
                    
                    if result_credit:
                        for r in result_credit:
                            if (r[4] >= str(start_p_start)) and (r[4] <= str(end_p_start)):
                                 cont_c = cont_c +1 
                    
                    if result_debit:
                        for r in result_debit:
                            if (r[4] >= str(start_p_start)) and (r[4] <= str(end_p_start)):
                                 cont_d = cont_d +1 
                    
                    if result_withholding:
                        for r in result_withholding:
                            if (r[4] >= str(start_p_start)) and (r[4]<= str(end_p_start)):
                                 cont_w = cont_w +1 
        else:
            if number != None:
                cur.execute("SELECT * FROM factura_web WHERE ruc = %s AND tipo ='out_invoice'", (number,))
                result_invoice = cur.fetchall()
                
                cur.execute("SELECT * FROM factura_web WHERE ruc = %s AND tipo ='out_credit_note'", (number,))
                result_credit = cur.fetchall()
                
                cur.execute("SELECT * FROM factura_web WHERE ruc = %s AND tipo ='out_debit_note'", (number,))
                result_debit = cur.fetchall()
                
                cur.execute("SELECT * FROM factura_web WHERE ruc = %s AND tipo ='in_withholding'", (number,))
                result_withholding = cur.fetchall()
                
                if result_invoice:
                    for r in result_invoice:
                        cont = cont +1 
                
                if result_credit:
                    for r in result_credit:
                        cont_c = cont_c +1 
                
                if result_debit:
                    for r in result_debit:
                        cont_d = cont_d +1 
                
                if result_withholding:
                    for r in result_withholding:
                        cont_w = cont_w +1 
            
            else: 
                cur.execute("SELECT * FROM factura_web WHERE tipo ='out_invoice'")
                result_invoice = cur.fetchall()
                cur.execute("SELECT * FROM factura_web WHERE tipo ='out_credit_note'")
                result_credit = cur.fetchall()
                 
                cur.execute("SELECT * FROM factura_web WHERE tipo ='out_debit_note'")
                result_debit = cur.fetchall()
                
                cur.execute("SELECT * FROM factura_web WHERE tipo ='in_withholding'")
                result_withholding = cur.fetchall()
                
                if result_invoice:
                    for r in result_invoice:
                        cont = cont +1 
                
                if result_credit:
                    for r in result_credit:
                        cont_c = cont_c +1 
                
                if result_debit:
                    for r in result_debit:
                        cont_d = cont_d +1 
                
                if result_withholding:
                    for r in result_withholding:
                        cont_w = cont_w +1 
        
        if cont < 1001:
            value_invoice = cont * value_1
        elif cont < 10001:
            value_invoice = cont * value_2
        elif cont < 50001:
            value_invoice = cont * value_3
        elif cont > 50001:
            value_invoice = cont * value_4
            
        if cont_c < 1001:
            value_credit = cont_c * value_1
        elif cont_c < 10001:
            value_credit = cont_c * value_2
        elif cont_c < 50001:
            value_credit = cont_c * value_3
        elif cont_c > 50001:
            value_credit = cont_c * value_4
            
        if cont_d < 1001:
            value_debit = cont_d  * value_1
        elif cont_d  < 10001:
            value_debit = cont_d  * value_2
        elif cont_d  < 50001:
            value_debit = cont_d  * value_3
        elif cont_d  > 50001:
            value_debit = cont_d  * value_4
            
        if cont_w < 1001:
            value_withholding = cont_w * value_1
        elif cont_w < 10001:
            value_withholding = cont_w * value_2
        elif cont_w < 50001:
            value_withholding = cont_w * value_3
        elif cont_w > 50001:
            value_withholding = cont_w * value_4
            
        if cont_s < 1001:
            value_shipment = cont_s * value_1
        elif cont_s < 10001:
            value_shipment = cont_s * value_2
        elif cont_s < 50001:
            value_shipment = cont_s * value_3
        elif cont_s > 50001:
            value_shipment = cont_s * value_4
            
        total_value = value_invoice +  value_credit + value_debit + value_withholding + value_shipment
        total_voucher = cont + cont_c + cont_d + cont_w + cont_s 
        
        if party.id != None:
            localcontext['party'] = party.name
            localcontext['id'] = party.vat_number
        else:
            localcontext['party'] = "Reporte de comprobantes de todos los clientes"
            localcontext['id'] = ""
            
        localcontext['contador_invoice'] = cont
        localcontext['contador_credit'] = cont_c
        localcontext['contador_debit'] = cont_d
        localcontext['contador_withholding'] = cont_w
        localcontext['contador_shipment'] = cont_s
        localcontext['total_voucher'] = total_voucher
        localcontext['value_invoice'] = value_invoice
        localcontext['value_credit'] = value_credit
        localcontext['value_debit'] = value_debit
        localcontext['value_withholding'] = value_withholding
        localcontext['value_shipment'] = value_shipment
        localcontext['total_value'] = total_value
        if start.id != None:
            localcontext['inicio'] = start.start_date
        else:
            localcontext['inicio'] = fiscal.start_date
        if end.id != None:
            localcontext['fin']= end.end_date
        else:
            localcontext['fin']= fiscal.end_date
            
        """
        address = party.cabecera+"://"+base64.decodestring(party.usuario)+":"+base64.decodestring(party.pass_db)+"@"+party.direccion+":"+party.puerto+"/"+base64.decodestring(party.name_db)
        
        s= xmlrpclib.ServerProxy(address)
        
        invoice, credit, debit, withholding, shipment = s.model.account.invoice.count_invoice(number, start_p_start, end_p_start, start_p_end, end_p_end, {})
        
        total_voucher = invoice + credit + debit + withholding + shipment
        """
        return super(TotalVoucher, cls).parse(report, objects, data, 
            localcontext)
