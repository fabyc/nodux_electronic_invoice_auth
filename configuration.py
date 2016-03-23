#This file is part of Tryton.  The COPYRIGHT file at the top level of
#this repository contains the full copyright notices and license terms.
from trytond.model import ModelView, ModelSQL, ModelSingleton, fields
from trytond.pool import Pool, PoolMeta
from trytond.transaction import Transaction
from trytond.pyson import Eval
from decimal import Decimal

__all__ = ['Configuration']
__metaclass__ = PoolMeta

class Configuration():
    'Account Configuration'
    __name__ = 'account.configuration'
    
    value_1 = fields.Numeric('Valor de 0 a 1000 comprobantes') 
    value_2 = fields.Numeric('Valor de 1001 a 10000 comprobantes') 
    value_3 = fields.Numeric('Valor de 10001 a 50000 comprobantes') 
    value_4 = fields.Numeric('Mas de 50001 comprobantes') 
    
    @staticmethod
    def default_value_1():
        print "Ingresa pero no asigna"
        return Decimal(0.08)
        
    @staticmethod
    def default_value_2():
        return Decimal(0.06)
    
    @staticmethod
    def default_value_3():
        return Decimal(0.04)
    
    @staticmethod
    def default_value_4():
        return Decimal(0.03)
