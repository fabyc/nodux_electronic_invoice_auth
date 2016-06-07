# -*- coding: utf-8 -*-
import commands
import logging
import smtplib, os
import StringIO
import string
import base64
import psycopg2
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
import shutil
from email.MIMEMultipart import MIMEMultipart
from email.MIMEText import MIMEText
from email.MIMEBase import MIMEBase
from email.mime.application import MIMEApplication
from email import encoders
from email.Utils import COMMASPACE, formatdate
from email import Encoders
import os.path

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

NUEVA_RUTA = '/var/www/vhosts/nodux.ec/.noduxenvs/nodux34auth'

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
        cls.__rpc__['save_file']=RPC(check_access=False)
        cls.__rpc__['connect_db']=RPC(check_access=False)
        cls.__rpc__['check_digital_signature']=RPC(check_access=False)
        cls.__rpc__['path_files'] = RPC(check_access=False)
        cls.__rpc__['send_mail'] = RPC(check_access=False)
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
        a = Date.today()
        if user:
            flag = '1'
            flag_c = '0'
            flag_a = '0'
            for u in user:
                c = u.correo
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
            limit= (date-a).days
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
        #nuevaruta =os.getcwd() +'/certificados'
        nuevaruta = NUEVA_RUTA + '/certificados'
        if not os.path.exists(nuevaruta):
            os.makedirs(nuevaruta)
        return nuevaruta
        
    @classmethod
    def path_files(cls, ruc):
        #nuevaruta = os.getcwd() +'/comprobantes/'
        nuevaruta = NUEVA_RUTA + '/comprobantes/'
        return nuevaruta

    @classmethod
    def send_mail(cls, name_pdf, name, p_xml, p_pdf, from_email, to_email, n_tipo, num_fac, client, empresa_, ruc):
        Company = Pool().get('company.company')
        companys = Company.search([('id', '!=', None)])

        correos = Pool().get('party.contact_mechanism')
        correo = correos.search([('type','=','email')])

        for c in companys:
            company = c
        if company:
            servidor = company.servidor
            puerto = company.puerto
            password = company.password

        for mail in correo:
            if mail.party == company.party:
                fromaddr = mail.value

        #fromaddr= from_email
        toaddr= to_email
        msg = MIMEMultipart()
        msg['From'] = fromaddr
        msg['To'] = (toaddr)
        msg['Date'] = formatdate(localtime=True)
        msg['Subject'] = n_tipo + ' '+num_fac
        html = """\
                    <!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
                    <html xmlns="http://www.w3.org/1999/xhtml">
                     <head>
                    <meta http-equiv="Content-Type" content="text/html; charset=UTF-8" />
                    <title>Comprobantes Electrónicos</title>
                    <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
                    </head>
                    <body style="margin: 0; padding: 10;">
                     <table border="0" cellpadding="0" cellspacing="0" width="100%">
                    <tr>
                     <td>
                    <table align="center" border="0" cellpadding="0" cellspacing="0" width="600">
                     <tr>
                    <td align="center" bgcolor="#C61F34" style="color: #ffffff; font-family: Verdana, sans-serif; font-size: 20px; padding: 40px 0 30px 0; border-radius: 5px;"><IMG SRC="ftp://nodux.ec/img/logo.png" ALT="NODUX Cía. Ltda.">
                    <p>
                    Sistema Experto en Gestión Empresarial
                    </td>
                     </tr>
                     <tr>
                    <td bgcolor="#ffffff" style="padding: 40px 30px 40px 30px;">
                     <table border="0" cellpadding="0" cellspacing="0" width="100%">
                     <tr>
                    <td style="color: #153643; font-family: Arial, sans-serif; font-size: 14px;">
                    <b> Estimado(a) {client} :</b>
                    <p>
                    </td>
                     </tr>
                     <tr>
                    <td style="color: #153643; font-family: Arial, sans-serif; font-size: 14px; line-height: 20px;">
                    <p>
                    Nodux le informa que {empresa_} le ha emitido un comprobante electrónico: {n_tipo} {num_fac}, el cual está disponible para su visualización y descarga.
                    <p>
                      Para consultar sus comprobantes electrónicos diríjase a:  <a href= "http://nodux.ec:8085/" style="color: #C61F34;">comprobantes.nodux.ec</a>. No olvide ingresar como usuario y contraseña  su número de identificación (cedula o ruc)
                    </td>
                     </tr>
                     <tr>
                    <td style="padding: 20px 0 30px 0; color: #153643; font-family: Arial, sans-serif; font-size: 12px; line-height: 20px;">
                     <b>Recuerde: </b> La representación impresa del comprobante electrónico es el archivo PDF adjunto. Posee validez tributaria y podrá imprimirlo solamente en los casos que el SRI lo dispone.
                    </td>
                     </tr>
                    </table>
                    </td>
                     </tr>
                     <tr>
                     <td bgcolor="#C61F34" style="padding: 30px 30px 30px 30px; color: #153643; font-family: Arial, sans-serif; font-size:13px; line-height: 20px; border-radius: 5px">
                     <table border="0" cellpadding="0" cellspacing="0" width="100%">
                     <tr>
                    <td style="color: #ffffff; font-family: Arial, sans-serif; font-size: 14px;">
                     &reg; Nodux. Cía. Ltda. 2016<br/>
                    </td>
                    <td>
                     <td align="right" width "25%" style="color: #153643; font-family: Arial, sans-serif; font-size: 13px; line-height: 20px;">
                     <table border="0" cellpadding="0" cellspacing="0">
                    <tr>
                     <td style="color: #ffffff; font-family: Arial, sans-serif; font-size: 13px; line-height: 20px;">
                      <a href="www.twitter.com/noduxEC"> Twitter
                      </a>
                     </td>
                     <td style="font-size: 0; line-height: 0;" width="20">&nbsp;</td>
                     <td>
                      <a href="www.facebook.com/nodux/info?tab=overview"> Facebook
                      </a>
                     </td>
                    </tr>
                     </table>
                    </td>
                    </td>
                     </tr>
                    </table>
                    </td>
                     </tr>
                    </table>
                     </td>
                    </tr>
                     </table>
                    </body>
                    </html>
                    """.format(client=client, empresa_=empresa_, n_tipo=n_tipo, num_fac=num_fac)
        pdf = MIMEApplication(open(p_pdf).read())
        pdf.add_header('Content-Disposition', 'attachment', filename=name_pdf)
        xml = MIMEApplication(open(p_xml).read())
        xml.add_header('Content-Disposition', 'attachment', filename=name)
        msg.attach(MIMEText(html, 'html'))
        msg.attach(xml)
        msg.attach(pdf)
        #msg.attach(part2)
        server = smtplib.SMTP('smtp.gmail.com:587')
        server.starttls()
        server.login(fromaddr, password)
        text = msg.as_string()
        server.sendmail(fromaddr, toaddr, text)
        server.quit()

        return True

    @classmethod
    def save_file(cls,  empresa, name_pdf, name_xml, report, xml_element):
        ahora = datetime.datetime.now()
        year = str(ahora.year)
        if ahora.month < 10:
            month = '0'+ str(ahora.month)
        else:
            month = str(ahora.month)
        #nuevaruta_c =os.getcwd() +'/comprobantes/'+empresa +'/'+year+'/'+month
        nuevaruta_c = NUEVA_RUTA + '/comprobantes/'+empresa +'/'+year+'/'+month
        if not os.path.exists(nuevaruta_c):
            os.makedirs(nuevaruta_c)
        file_ = 'true'
        f = open(nuevaruta_c + "/" + name_pdf, 'wb')
        f.write(report)
        f.close()
        f = open(nuevaruta_c + "/" + name_xml, 'wb')
        f.write(xml_element)
        f.close()
        
        commands.getoutput('rsync -az /home/noduxdev/.noduxenvs/nodux34auth/comprobantes/* /home/noduxdev/pruebas/comprobantes/')
        #shutil.copy2(name_pdf, nuevaruta_c)
        #shutil.copy2(name_xml, nuevaruta_c)
        #os.remove(name_pdf)
        #os.remove(name_xml)

        return file_

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
    def check_digital_signature(cls, file_pk12):
        #xml_str = etree.tostring(xml_document, encoding='utf8', method='xml')
        error = '0'
        if os.path.exists(file_pk12):
            pass
        else:
            error = '1'
        return error

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
                if m.identificador == '43' :
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

        #nuevaruta =os.getcwd()+'/comprobantes/'+empresa+'/'+year+'/'+month
        nuevaruta = NUEVA_RUTA + '/comprobantes/'+empresa+'/'+year+'/'+month

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
            etree.SubElement(autorizacion_xml, 'ambiente').text = 'PRODUCCION' #autorizacion.ambiente.replace("Ó","O") #Nodux autorizacion.ambiente
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

        #nuevaruta =os.getcwd()+'/comprobantes/'+empresa+'/'+year+'/'+month
        nuevaruta = NUEVA_RUTA+'/comprobantes/'+empresa+'/'+year+'/'+month

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

    @classmethod
    def connect_db(cls, nombre, cedula, ruc, nombre_e, tipo, fecha, empresa, numero, path_xml, path_pdf,estado, auth, email, email_e, total):

        conn = psycopg2.connect(user="noduxappweb", password="ndxapwb0980", host="localhost", dbname="noduxcompelect")
        #conn = psycopg2.connect("dbname=usuarios_web")
        cur = conn.cursor()
        cur.execute("SELECT * FROM information_schema.sequences")
        sequences = cur.fetchall()
        s_true_u = 0
        s_true_f = 0
        for s in sequences:
            if s[2] == 'user_id_seq':
                s_true_u = 1
            elif s[2] == 'factura_id_seq':
                s_true_f = 1
            else:
                pass
        if s_true_u == 0:
            cur.execute("CREATE SEQUENCE user_id_seq;")
        if s_true_f == 0:
            cur.execute("CREATE SEQUENCE factura_id_seq;")
        cur.execute("CREATE TABLE IF NOT EXISTS usuario_web (id integer DEFAULT  NEXTVAL('user_id_seq') NOT  NULL, username varchar, password varchar, cedula varchar, correo varchar, nombre varchar, token varchar, fecha varchar, primary key (id))")
        cur.execute("CREATE TABLE IF NOT EXISTS factura_web (id integer DEFAULT  NEXTVAL('factura_id_seq') NOT  NULL, cedula varchar, ruc varchar, tipo varchar, fecha varchar, empresa varchar, numero_comprobante varchar, numero_autorizacion varchar, total varchar, path_xml varchar, path_pdf varchar, primary key (numero_autorizacion))")
        conn.commit()

        cur.execute("SELECT username FROM usuario_web WHERE cedula = %s", (cedula,))
        result = cur.fetchone()
        if result:
            pass
        else:
            cur.execute("INSERT INTO usuario_web (username, password, cedula, correo, nombre) VALUES (%s, %s, %s, %s, %s)",(cedula,cedula, cedula, email, nombre))
            conn.commit()

        cur.execute("SELECT username FROM usuario_web WHERE cedula = %s", (ruc,))
        result = cur.fetchone()
        if result:
            pass
        else:
            cur.execute("INSERT INTO usuario_web (username, password, cedula, correo, nombre) VALUES (%s, %s, %s, %s, %s)",(ruc,ruc, ruc, email_e, nombre_e))
            conn.commit()

        cur.execute("SELECT cedula FROM factura_web WHERE numero_autorizacion = %s", (auth,))
        result = cur.fetchone()
        if result:
            pass
        else:
            cur.execute("INSERT INTO factura_web (cedula, ruc, tipo, fecha, empresa, numero_comprobante, numero_autorizacion, total, path_xml, path_pdf) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",(cedula, ruc, tipo, fecha, empresa, numero, auth, total, path_xml, path_pdf))
            conn.commit()
        cur.close()
        conn.close()

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
        return self.get_env_prod()

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
