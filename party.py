#! -*- coding: utf8 -*-

from trytond.model import ModelView, ModelSQL, fields, Workflow
from trytond.pyson import Eval
from trytond.pool import Pool, PoolMeta
import base64
from decimal import Decimal
__all__ = ['Party']

__metaclass__ = PoolMeta

class Party(ModelSQL, ModelView):
    'Party'
    __name__ = 'party.party'
   
    correo = fields.Boolean(u'Utilizar correo de la empresa?', help= "Se utilizara el correo de la empresa emisora \n para enviar comprobantes electronicos a los clientes")
    passwordws = fields.Char('Password WS', help='Ingrese el password que le fue emitido por la empresa')
    userws = fields.Char('Usuario WS', help='Ingrese el usuario que le fue emitido por la empresa')
    password = fields.Function(fields.Char('Password WS'), getter='get_password', setter='set_password')
    user = fields.Function(fields.Char('Usuario WS'), getter='get_user', setter='set_user')
    date_active = fields.Date('Fecha limite activo')
    value_1 = fields.Numeric('Valor de 0 a 1000 comprobantes') 
    value_2 = fields.Numeric('Valor de 1001 a 10000 comprobantes') 
    value_3 = fields.Numeric('Valor de 10001 a 50000 comprobantes') 
    value_4 = fields.Numeric('Mas de 50001 comprobantes') 
    
    @staticmethod
    def default_value_1():
        pool = Pool()
        Config = pool.get('account.configuration')
        w = Config(1).value_1
        return w
          
    @staticmethod
    def default_value_2():
        pool = Pool()
        Config = pool.get('account.configuration')
        w = Config(1).value_2
        return w
    
    @staticmethod
    def default_value_3():
        pool = Pool()
        Config = pool.get('account.configuration')
        w = Config(1).value_3
        return w
    
    @staticmethod
    def default_value_4():
        pool = Pool()
        Config = pool.get('account.configuration')
        w = Config(1).value_4
        return w
        
        
    def get_password(self, name):
        return 'x' * 10
    
    @classmethod
    def set_password(cls, partys, name, value):
        if value == 'x' * 10:
            return
        to_write = []
        for party in partys:
            to_write.extend([[party], {
                        'passwordws': base64.encodestring(value),
                        }])
        cls.write(*to_write)
        

    def get_user(self, name):
        return 'x' * 10
    
    @classmethod
    def set_user(cls, partys, name, value):
        if value == 'x' * 10:
            return
        to_write = []
        for party in partys:
            to_write.extend([[party], {
                        'userws': base64.encodestring(value),
                        }])
        cls.write(*to_write)
        
