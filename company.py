#! -*- coding: utf8 -*-

from trytond.model import ModelView, ModelSQL, fields, Workflow
from trytond.pyson import Eval
from trytond.pool import Pool, PoolMeta
import base64
from decimal import Decimal
from trytond.pyson import Id

__all__ = ['Company']
__metaclass__ = PoolMeta


class Company():
    'Company'
    __name__ = 'company.company'

    servidor = fields.Char('Servidor SMTP', required = True)
    puerto = fields.Char('Puerto', required=True)
    password = fields.Char('Password correo electronico', required= True)

    @classmethod
    def __setup__(cls):
        super(Company, cls).__setup__()

    @classmethod
    def default_currency(cls):
        Currency = Pool().get('currency.currency')
        usd= Currency.search([('code','=','USD')])
        return usd[0].id

    @staticmethod
    def default_timezone():
        return 'America/Guayaquil'

    @staticmethod
    def default_servidor():
        return 'smtp.gmail.com'

    @staticmethod
    def default_puerto():
        return '587'
