# -*- coding: utf-8 -*-

import logging
import os
import StringIO
import string
import base64
import xmlrpclib
from SimpleXMLRPCServer import SimpleXMLRPCServer
from trytond.rpc import RPC
import hashlib
import datetime
import subprocess
import random
from trytond.modules.company import CompanyReport
from lxml import etree
from pytz import timezone
from trytond.pool import Pool, PoolMeta
import datetime

USER = 'admin'
PASSWORD = 'pruebasfacturacion' 

from lxml import etree
from lxml.etree import DocumentInvalid
try:
    from OpenSSL import crypto
except ImportError:
    raise ImportError('Instalar la libreria para soporte OpenSSL: pip install PyOpenSSL')
    
try:
    from ctypes import *
except ImportError:
    raise ImportError('Libreria CTypes no esta disponible')

try:
    from suds.client import Client
    from suds.transport import TransportError
except ImportError:
    raise ImportError('Instalar Libreria suds')

import utils
from trytond.pool import Pool, PoolMeta, Transaction
from trytond.model import fields, ModelSQL, ModelView

SCHEMAS = {
    'out_invoice': 'schemas/factura.xsd',
    'out_credit_note': 'schemas/notaCredito.xsd',
    'in_withholding': 'schemas/comprobanteRetencion.xsd',
    'out_debit_note': 'schemas/notaDebito.xsd',
    'out_shipment' : 'schemas/guiaRemision.xsd',
    'lote':'schemas/lote.xsd'
}
__all__ = ['DocumentXML']

class DocumentXML(ModelSQL, ModelView):
    "DocumentXML"
    __name__ = "nodux_electronic_invoice_auth.conexiones"
 
    number_out_invoice = fields.Integer(u'Total de Facturas')
    number_out_credit_note = fields.Integer(u'Total de Notas de Crédito')
    number_in_withholding = fields.Integer(u'Total de Comprobantes de Retención')
    number_out_debit_note = fields.Integer(u'Total de Notas de Débito')
    number_out_shipment = fields.Integer(u'Total de Guías de Remisión')
    
    @classmethod
    def __setup__(cls):
        super(DocumentXML, cls).__setup__()
        cls.__rpc__['validate_xml'] = RPC(check_access=False)
        cls.__rpc__['apply_digital_signature']=RPC(check_access=False)
        cls.__rpc__['send_receipt']=RPC(check_access=False)
        cls.__rpc__['request_authorization']=RPC(check_access=False)
        cls.__rpc__['request_authorization_lote']=RPC(check_access=False)
        cls.__rpc__['count_voucher']=RPC(check_access=False)
        cls.__rpc__['authenticate']=RPC(check_access=False)
        cls.__rpc__['save_pk12']=RPC(check_access=False)
        cls._error_messages.update({
                'no_autorizado': ('Verifique su usuario y password, para acceder al sistema'),
                })
        
    @classmethod
    def authenticate(cls, user, password):
        pool = Pool()
        users = pool.get('party.party')
        user = users.search([('userws','=', user), ('passwordws', '=', password)])
        Date = pool.get('ir.date')
        c = False
        
        if user:
            flag = '1'
            for u in user:
                c = u.correo
                print "El correo ", c
                a = u.date_active
        else:
            flag = '0'
            flag_c = '0'
            flag_a = '0'
            
        if c == True:
            flag_c = '1'
        else:
            flag_c = '0'
            
        if a:
            date= Date.today()
            print "Fecha hoy",date
            print "Fecha limite",a
            limit= (date-a).days
            print "Fechas limites ", limit
            if limit > 5:
                flag_a = '1' 
            else: 
                flag_a = '0'   
                    
            return flag, flag_c, flag_a
    @classmethod
    def check_password(cls, password, hash_):
        if not hash_:
            return False
        hash_method = hash_.split('$', 1)[0]
        return getattr(cls, 'check_' + hash_method)(password, hash_)
        
    @classmethod
    def check_sha1(cls, password, hash_):
        if isinstance(password, unicode):
            password = password.encode('utf-8')
        if isinstance(hash_, unicode):
            hash_ = hash_.encode('utf-8')
        hash_method, hash_, salt = hash_.split('$', 2)
        salt = salt or ''
        assert hash_method == 'sha1'
        return hash_ == hashlib.sha1(password + salt).hexdigest()
        
    @classmethod
    def save_pk12(cls, empresa):
        ahora = datetime.datetime.now()
        year = str(ahora.year)
        if ahora.month < 10:
            month = '0'+ str(ahora.month)
        else:
            month = str(ahora.month)
        nuevaruta =os.getcwd() +'/certificados'
        nuevaruta_c =os.getcwd() +'/comprobantes/'+empresa +'/'+year+'/'+month
        if not os.path.exists(nuevaruta): 
            os.makedirs(nuevaruta)
        if not os.path.exists(nuevaruta_c): 
            os.makedirs(nuevaruta_c)
        return nuevaruta
              
    @classmethod
    def validate_xml(cls, document, type_document):
        schema = SCHEMAS[type_document]
        message_invalid = u"El sistema generó el XML pero el comprobante electrónico no pasa el formato. Revise los campos de su factura"
        file_path = os.path.join(os.path.dirname(__file__), schema)
        schema_file = open(file_path, 'r')        
        xmlschema_doc = etree.parse(schema_file)
        xmlschema = etree.XMLSchema(xmlschema_doc)
        document= etree.fromstring(document)
        try:
            xmlschema.assertValid(document)
        except DocumentInvalid as e:
            print e
            print ('Error de Datos', message_invalid)
            return (message_invalid+str(e))
        
    @classmethod
    def apply_digital_signature(cls, xml_document, file_pk12, password):
        #xml_str = etree.tostring(xml_document, encoding='utf8', method='xml')
        firma_path = os.path.join(os.path.dirname(__file__), 'firma/firmaXadesBes.jar')        
        p = subprocess.Popen(['java', '-jar', firma_path, xml_document, file_pk12, password], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        res = p.communicate()
        print res
        return res[0]
    
    @classmethod        
    def send_receipt(cls, document):
        buf = StringIO.StringIO()
        buf.write(document)
        buffer_xml = base64.encodestring(buf.getvalue())
        if not utils.check_service('prueba'):
            print ('Error SRI', 'Servicio SRI no disponible.')

        client = Client(SriService.get_active_ws()[0])
        result =  client.service.validarComprobante(buffer_xml)
        print result
        
        if result[0] == 'RECIBIDA':
            return True
        else:
            for m in result[1][0][0][1][0]:
                if m.identificador == '43':
                    return True
                else:        
                    response = u'Comprobante Electrónico DEVUELTO:\nError : ' +str(m.mensaje) + '\nIdentificador : ' +str(m.identificador)
                    return response
            
    @classmethod
    def request_authorization(cls, access_key, empresa, tipo_comprobante):
        messages = []
        m = ""
        client = Client(SriService.get_active_ws()[1])
        result =  client.service.autorizacionComprobante(access_key)
        print "El resultado ",result
        ruta_actual = os.path.join(os.path.dirname(__file__))
        autorizacion = result.autorizaciones[0][0]
        ahora = datetime.datetime.now()
        year = str(ahora.year)
        if ahora.month < 10:
            month = '0'+ str(ahora.month)
        else:
            month = str(ahora.month)
        if tipo_comprobante == 'out_invoice':
            tipo = 'fact_'
        if tipo_comprobante == 'in_withholding':
            tipo = 'c_r'
        if tipo_comprobante == 'out_credit_note':
            tipo = 'n_c'
        if tipo_comprobante == 'out_debit_note':
            tipo = 'n_d'
        
        nuevaruta =os.getcwd()+'/comprobantes/'+empresa+'/'+year+'/'+month
        
        if autorizacion.estado == 'AUTORIZADO':
            num = str(autorizacion.numeroAutorizacion)
            ruc = num[10:23]
            est = num[24:27] 
            emi= num[27:30]
            sec = num[30:39]
            numero = ruc+'_'+est+'-'+emi+'-'+sec
            ruta_db = os.getcwd()+'/comprobantes/'+empresa+'/'+ year+'/'+month +'/'+tipo+numero 
            autorizacion_xml = etree.Element('autorizacion')
            etree.SubElement(autorizacion_xml, 'estado_sri').text = autorizacion.estado
            etree.SubElement(autorizacion_xml, 'numeroAutorizacion').text = autorizacion.numeroAutorizacion
            etree.SubElement(autorizacion_xml, 'ambiente').text = autorizacion.ambiente
            etree.SubElement(autorizacion_xml, 'comprobante').text = etree.CDATA(autorizacion.comprobante)
            autorizacion_xml = etree.tostring(autorizacion_xml, encoding = 'utf8', method = 'xml')
            messages=" ".join(messages)
            auth = autorizacion.estado
            if not os.path.exists(nuevaruta): 
                os.makedirs(nuevaruta)
            
            return autorizacion_xml, False, 'AUTORIZADO' , ruta_db, numero, num
        else:
            for m in autorizacion.mensajes[0]:
                messages.append(m.identificador)
                messages.append(m.mensaje)
                messages=",".join(messages)
                response = u'Comprobante Electrónico NO AUTORIZADO:\nError : ' +str(m.mensaje) + '\nIdentificador : ' +str(m.identificador)
            return False, response, False , False, False, False

    @classmethod        
    def request_authorization_lote(cls, access_key, empresa, tipo_comprobante):
        messages = []
        m = ""
        
        client = Client(SriService.get_active_ws()[1])
        result =  client.service.autorizacionComprobante(access_key)
        print "El resultado ",result
        ruta_actual = os.path.join(os.path.dirname(__file__))
        autorizacion = result.autorizaciones[0][0]
        ahora = datetime.datetime.now()
        year = str(ahora.year)
        if ahora.month < 10:
            month = '0'+ str(ahora.month)
        else:
            month = str(ahora.month)
        if tipo_comprobante == 'lote_out_invoice':
            tipo = 'lote_fact_'
        if tipo_comprobante == 'lote_out_withholding':
            tipo = 'lote_c_r_'
        if tipo_comprobante == 'lote_out_credit_note':
            tipo = 'lote_n_c_'
        if tipo_comprobante == 'lote_out_debit_note':
            tipo = 'lote_n_d_'
        if tipo_comprobante == 'lote_out_shipment':
            tipo = 'lote_g_r_'
        nuevaruta =os.getcwd()+'/comprobantes/'+empresa+'/'+year+'/'+month
        
        if autorizacion.estado == 'AUTORIZADO':
            num = str(autorizacion.numeroAutorizacion)
            ruc = num[10:23]
            est = num[24:27] 
            emi= num[27:30]
            sec = num[30:39]
            numero = ruc+'_'+est+'-'+emi+'-'+sec
            ruta_db = os.getcwd()+'/comprobantes/'+empresa+'/'+ year+'/'+month +'/'+tipo+numero 
            autorizacion_xml = etree.Element('autorizacion')
            etree.SubElement(autorizacion_xml, 'estado_sri').text = autorizacion.estado
            etree.SubElement(autorizacion_xml, 'numeroAutorizacion').text = autorizacion.numeroAutorizacion
            etree.SubElement(autorizacion_xml, 'ambiente').text = autorizacion.ambiente
            etree.SubElement(autorizacion_xml, 'comprobante').text = etree.CDATA(autorizacion.comprobante)
            autorizacion_xml = etree.tostring(autorizacion_xml, encoding = 'utf8', method = 'xml')
            messages=" ".join(messages)
            auth = autorizacion.estado
            if not os.path.exists(nuevaruta): 
                os.makedirs(nuevaruta)
            return autorizacion_xml, False, 'AUTORIZADO' , ruta_db, numero, num
        else:
            for m in autorizacion.mensajes[0]:
                messages.append(m.identificador)
                messages.append(m.mensaje)
                messages=",".join(messages)
                response = u'Comprobante Electrónico NO AUTORIZADO:\nError : ' +str(m.mensaje) + '\nIdentificador : ' +str(m.identificador)
            return False, response, False , False, False
            
class SriService(object):

    __AMBIENTE_PRUEBA = '1'
    __AMBIENTE_PROD = '2'
    __WS_TEST_RECEIV = 'https://celcer.sri.gob.ec/comprobantes-electronicos-ws/RecepcionComprobantesOffline?wsdl'
    __WS_TEST_AUTH = 'https://celcer.sri.gob.ec/comprobantes-electronicos-ws/AutorizacionComprobantesOffline?wsdl'
    __WS_RECEIV = 'https://cel.sri.gob.ec/comprobantes-electronicos-ws/RecepcionComprobantesOffline?wsdl'
    __WS_AUTH = 'https://cel.sri.gob.ec/comprobantes-electronicos-ws/AutorizacionComprobantesOffline?wsdl'
    
    __WS_TESTING = (__WS_TEST_RECEIV, __WS_TEST_AUTH)
    __WS_PROD = (__WS_RECEIV, __WS_AUTH)
    __WS_ACTIVE = __WS_TESTING

    @classmethod
    def get_active_env(self):
        return self.get_env_test()

    @classmethod
    def get_env_test(self):
        return self.__AMBIENTE_PRUEBA

    @classmethod
    def get_env_prod(self):
        return self.__AMBIENTE_PROD

    @classmethod
    def get_ws_test(self):
        return self.__WS_TEST_RECEIV, self.__WS_TEST_AUTH
    
    @classmethod
    def get_ws_prod(self):
        return self.__WS_RECEIV, self.__WS_AUTH

    @classmethod
    def get_active_ws(self):
        return self.__WS_ACTIVE
        
