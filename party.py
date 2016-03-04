#! -*- coding: utf8 -*-

from trytond.model import ModelView, ModelSQL, fields, Workflow
from trytond.pyson import Eval
from trytond.pool import Pool, PoolMeta
import base64

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
    
    @staticmethod
    def default_lote():
        return False
        
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
        
