#! -*- coding: utf8 -*-

from trytond.model import ModelView, ModelSQL, fields, Workflow
from trytond.pyson import Eval
from trytond.pool import Pool, PoolMeta
import base64
from decimal import Decimal
from trytond.pyson import Id

__all__ = ['Party', 'Address', 'Configuration']
__metaclass__ = PoolMeta

class Party():
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
    type_document = fields.Selection([
                ('', ''),
                ('04', 'RUC'),
                ('05', 'Cedula'),
                ('06', 'Pasaporte'),
                ('07', 'Consumidor Final'),
            ], 'Type Document', states={
                'readonly': ~Eval('active', True),
            },  depends=['active'])


    @classmethod
    def __setup__(cls):
        super(Party, cls).__setup__()
        cls._error_messages.update({
                'invalid_vat_number': ('Invalid VAT Number "%s".')})
        cls._sql_constraints += [
            ('vat_number', 'UNIQUE(vat_number)',
                'VAT Number already exists!'),
        ]


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

    @classmethod
    def search_rec_name(cls, name, clause):
        parties = cls.search([
                ('vat_number',) + tuple(clause[1:]),
                ], limit=1)
        if parties:
            return [('vat_number',) + tuple(clause[1:])]
        return [('name',) + tuple(clause[1:])]

    @classmethod
    def validate(cls, parties):
        for party in parties:
            if party.type_document == '04' and bool(party.vat_number):
                super(Party, cls).validate(parties)

    def pre_validate(self):
        if self.type_document == '':
            pass
        elif self.type_document == '06':
            pass
        else:
            if not self.vat_number:
                return
            if self.vat_number == '9999999999999':
                return
            vat_number = self.vat_number.replace(".", "")
            if vat_number.isdigit() and len(vat_number) > 9:
                is_valid = self.compute_check_digit(vat_number)
                if is_valid:
                    return
            self.raise_user_error('invalid_vat_number', (self.vat_number,))

    def compute_check_digit(self, raw_number):
        factor = 2
        x = 0
        set_check_digit = None

        if self.type_document == '04':
            # Si es RUC valide segun el tipo de tercero
            if int(raw_number[2]) < 6:
                type_party='persona_natural'
            if int(raw_number[2]) == 6:
                type_party='entidad_publica'
            if int(raw_number[2]) == 9:
                type_party='persona juridica'

            if type_party == 'persona_natural':
                if len(raw_number) != 13 or int(raw_number[2]) > 5 or raw_number[-3:] != '001':
                    return
                number = raw_number[:9]
                set_check_digit = raw_number[9]
                for n in number:
                    y = int(n) * factor
                    if y >= 10:
                        y = int(str(y)[0]) + int(str(y)[1])
                    x += y
                    if factor == 2:
                        factor = 1
                    else:
                        factor = 2
                res = (x % 10)
                if res ==  0:
                    value = 0
                else:
                    value = 10 - (x % 10)
                return (set_check_digit == str(value))

            elif type_party == 'entidad_publica':
                if not len(raw_number) == 13 or raw_number[2] != '6' \
                    or raw_number[-3:] != '001':
                    return
                number = raw_number[:8]
                set_check_digit = raw_number[8]
                for n in reversed(number):
                    x += int(n) * factor
                    factor += 1
                    if factor == 8:
                        factor = 2
                value = 11 - (x % 11)
                if value == 11:
                    value = 0
                return (set_check_digit == str(value))

            else:
                if len(raw_number) != 13 or \
                    (type_party in ['persona_juridica'] \
                    and int(raw_number[2]) != 9) or raw_number[-3:] != '001':
                    return
                number = raw_number[:9]
                set_check_digit = raw_number[9]
                for n in reversed(number):
                    x += int(n) * factor
                    factor += 1
                    if factor == 8:
                        factor = 2
                value = 11 - (x % 11)
                if value == 11:
                    value = 0
                return (set_check_digit == str(value))
        else:
            #Si no tiene RUC valide: cedula, pasaporte, consumidor final (cedula)
            if len(raw_number) != 10:
                return
            number = raw_number[:9]
            set_check_digit = raw_number[9]
            for n in number:
                y = int(n) * factor
                if y >= 10:
                    y = int(str(y)[0]) + int(str(y)[1])
                x += y
                if factor == 2:
                    factor = 1
                else:
                    factor = 2
            res = (x % 10)
            if res ==  0:
                value = 0
            else:
                value = 10 - (x % 10)
            return (set_check_digit == str(value))

class Address:
    __name__ = 'party.address'

    @staticmethod
    def default_country():
        return Id('country', 'ec').pyson()

class Configuration:
    __name__ = 'party.configuration'

    @classmethod
    def default_party_lang(cls):
        Lang = Pool().get('ir.lang')
        langs = Lang.search([('code','=','es_EC')])
        return langs[0].id
