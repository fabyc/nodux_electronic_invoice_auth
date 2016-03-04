#This file is part of Tryton.  The COPYRIGHT file at the top level of
#this repository contains the full copyright notices and license terms.
from trytond.pool import Pool
from .conexiones import *
from .account import *
from .party import *

def register():
    Pool.register(
        DocumentXML,
        OpenTotalVoucher,
        Party,
        module='nodux_electronic_invoice_auth', type_='model')      
    Pool.register(
        OpenTotal,
        module='nodux_electronic_invoice_auth', type_='wizard')        
    Pool.register(
        TotalVoucher,
        module='nodux_electronic_invoice_auth', type_='report')
        
        