# -*- coding: utf-8 -*-
import base64
from datetime import datetime, date
from itertools import groupby
import requests
from xml.etree import ElementTree

from lxml import etree
from lxml.objectify import fromstring
from suds.client import Client
from odoo import _, api, fields, models
from odoo.tools import DEFAULT_SERVER_TIME_FORMAT
from odoo.tools.float_utils import float_compare
from odoo.tools.misc import html_escape
from odoo.exceptions import UserError, ValidationError

class Complemento(models.Model):
    _name = 'complemento'
    nodo = fields.Char(
        string='Nodo',
    )
    id_documento = fields.Char(
        string='id Documento',
    )
    serie = fields.Char(
        string='Serie',
    )
    folio = fields.Char(
        string='Folio',
    )
    modena = fields.Char(
        string='Moneda',
    )
    parcialidad = fields.Char(
        string='Parcialidad',
    )
    metodo = fields.Char(
        string='Metodo de pago',
    )
    s_anterior = fields.Float(
        string='Saldo anterior',
    )
    s_pagado = fields.Float(
        string='Saldo pagado',
    )
    s_insoluto = fields.Float(
        string='Saldo insoluto',
    )
    account_id = fields.Many2one(
        'account.payment',
        string='account payment',
    )


class pagos_pagos(models.Model):
    _inherit = 'account.payment'


    complemento_ids = fields.One2many(
        'complemento',
        'account_id',
        string='Complento',
    )
    carga_lineas = fields.Integer(
        string='Cargar lineas', default=False,
    )
    @api.model
    def l10n_mx_edi_get_pago_etree(self, cfdi):
        if not hasattr(cfdi, 'Complemento'):
            return None
        attribute = 'pago10:Pagos[1]'
        namespace = {'pago10': 'http://www.sat.gob.mx/Pagos'}
        node = cfdi.Complemento.xpath(attribute, namespaces=namespace)
        
        return node[0] if node else None

    @api.multi
    @api.depends('l10n_mx_edi_cfdi_name')
    def _compute_cfdi_values(self):
        """Fill the invoice fields from the cfdi values."""
        for rec in self:
            attachment_id = rec.l10n_mx_edi_retrieve_last_attachment()
            if not attachment_id:
                continue
            attachment_id = attachment_id[0]
            # At this moment, the attachment contains the file size in its 'datas' field because
            # to save some memory, the attachment will store its data on the physical disk.
            # To avoid this problem, we read the 'datas' directly on the disk.
            datas = attachment_id._file_read(attachment_id.store_fname)
            rec.l10n_mx_edi_cfdi = datas
            tree = rec.l10n_mx_edi_get_xml_etree(base64.decodestring(datas))
            tfd_node = rec.l10n_mx_edi_get_tfd_etree(tree)
            if tfd_node is not None:
                rec.l10n_mx_edi_cfdi_uuid = tfd_node.get('UUID')
            rec.l10n_mx_edi_cfdi_supplier_rfc = tree.Emisor.get(
                'Rfc', tree.Emisor.get('rfc'))
            rec.l10n_mx_edi_cfdi_customer_rfc = tree.Receptor.get(
                'Rfc', tree.Receptor.get('rfc'))
            certificate = tree.get('noCertificado', tree.get('NoCertificado'))
            rec.l10n_mx_edi_cfdi_certificate_id = self.env['l10n_mx_edi.certificate'].sudo().search(
                [('serial_number', '=', certificate)], limit=1)
            


    @api.model
    def complemento(self):
        #self.complemento_ids = [(5, 0, 0)]
        data = base64.decodestring(self.l10n_mx_edi_cfdi)
        root =ElementTree.fromstring(data)
        r1=[]
        if root:            
            for child in root.findall('{http://www.sat.gob.mx/cfd/3}Complemento'):
                for pagos in child:
                    for pago in pagos:                        
                        for doc in pago:
                            
                            
                            for inv in self.invoice_lines:
                                num = inv.invoice_id.journal_id.sequence_id.padding
                                if len(doc.attrib['Folio']) == num:
                                    num_fac = str(doc.attrib['Serie']) +str(doc.attrib['Folio'])
                                    if inv.invoice == num_fac  and inv.comision_col == False:                            
                                        values = {
                                        'nodo': 1,
                                        'id_documento':doc.attrib['IdDocumento'],
                                        'serie':doc.attrib['Serie'],
                                        'folio':doc.attrib['Folio'],
                                        'modena': doc.attrib['MonedaDR'],
                                        'parcialidad':doc.attrib['NumParcialidad'],
                                        'metodo':doc.attrib['MetodoDePagoDR'],
                                        's_anterior':doc.attrib['ImpSaldoAnt'],
                                        's_pagado':doc.attrib['ImpPagado'],
                                        's_insoluto':doc.attrib['ImpSaldoInsoluto'],
                                        'account_id':self.id
                                        }
                                        r1.append(values)
                                    if inv.invoice == num_fac and inv.comision_col == True:
                                        monto = float(doc.attrib['ImpPagado'])
                                        monto_final = round(monto,2)
                                        monto_fac = inv.allocation - inv.comision_cam
                                        monto_fac_final =  round(monto_fac,2)
                                        if inv.comision_cam == monto_final:
                                
                                            values = {
                                            'nodo': 2,
                                            'id_documento':doc.attrib['IdDocumento'],
                                            'serie':doc.attrib['Serie'],
                                            'folio':doc.attrib['Folio'],
                                            'modena': doc.attrib['MonedaDR'],
                                            'parcialidad':doc.attrib['NumParcialidad'],
                                            'metodo':doc.attrib['MetodoDePagoDR'],
                                            's_anterior':doc.attrib['ImpSaldoAnt'],
                                            's_pagado':doc.attrib['ImpPagado'],
                                            's_insoluto':doc.attrib['ImpSaldoInsoluto'],
                                            'account_id':self.id
                                            }
                                            r1.append(values)
                                        if monto_fac_final == monto_final:
                                            values = {
                                            'nodo': 1,
                                            'id_documento':doc.attrib['IdDocumento'],
                                            'serie':doc.attrib['Serie'],
                                            'folio':doc.attrib['Folio'],
                                            'modena': doc.attrib['MonedaDR'],
                                            'parcialidad':doc.attrib['NumParcialidad'],
                                            'metodo':doc.attrib['MetodoDePagoDR'],
                                            's_anterior':doc.attrib['ImpSaldoAnt'],
                                            's_pagado':doc.attrib['ImpPagado'],
                                            's_insoluto':doc.attrib['ImpSaldoInsoluto'],
                                            'account_id':self.id
                                            }
                                            r1.append(values)
                                else:
                                    folio =str(doc.attrib['Folio'])
                                    folio_comple = folio.zfill(num)
                                    num_fac_com = str(doc.attrib['Serie']) +str(folio_comple)
                                    print("fffff",num_fac_com)



                                    if inv.invoice == num_fac_com  and inv.comision_col == False:                            
                                        values = {
                                        'nodo': 1,
                                        'id_documento':doc.attrib['IdDocumento'],
                                        'serie':doc.attrib['Serie'],
                                        'folio':doc.attrib['Folio'],
                                        'modena': doc.attrib['MonedaDR'],
                                        'parcialidad':doc.attrib['NumParcialidad'],
                                        'metodo':doc.attrib['MetodoDePagoDR'],
                                        's_anterior':doc.attrib['ImpSaldoAnt'],
                                        's_pagado':doc.attrib['ImpPagado'],
                                        's_insoluto':doc.attrib['ImpSaldoInsoluto'],
                                        'account_id':self.id
                                        }
                                        r1.append(values)
                                    if inv.invoice == num_fac_com and inv.comision_col == True:
                                        monto = float(doc.attrib['ImpPagado'])
                                        monto_final = round(monto,2)
                                        monto_fac = inv.allocation - inv.comision_cam
                                        monto_fac_final =  round(monto_fac,2)
                                        if inv.comision_cam == monto_final:
                                
                                            values = {
                                            'nodo': 2,
                                            'id_documento':doc.attrib['IdDocumento'],
                                            'serie':doc.attrib['Serie'],
                                            'folio':doc.attrib['Folio'],
                                            'modena': doc.attrib['MonedaDR'],
                                            'parcialidad':doc.attrib['NumParcialidad'],
                                            'metodo':doc.attrib['MetodoDePagoDR'],
                                            's_anterior':doc.attrib['ImpSaldoAnt'],
                                            's_pagado':doc.attrib['ImpPagado'],
                                            's_insoluto':doc.attrib['ImpSaldoInsoluto'],
                                            'account_id':self.id
                                            }
                                            r1.append(values)
                                        if monto_fac_final == monto_final:
                                            values = {
                                            'nodo': 1,
                                            'id_documento':doc.attrib['IdDocumento'],
                                            'serie':doc.attrib['Serie'],
                                            'folio':doc.attrib['Folio'],
                                            'modena': doc.attrib['MonedaDR'],
                                            'parcialidad':doc.attrib['NumParcialidad'],
                                            'metodo':doc.attrib['MetodoDePagoDR'],
                                            's_anterior':doc.attrib['ImpSaldoAnt'],
                                            's_pagado':doc.attrib['ImpPagado'],
                                            's_insoluto':doc.attrib['ImpSaldoInsoluto'],
                                            'account_id':self.id
                                            }
                                            r1.append(values)
                       
            return r1
              

    @api.model
    def complemento_encavezado(self):
          #self.complemento_ids = [(5, 0, 0)]
        data = base64.decodestring(self.l10n_mx_edi_cfdi)
        root =ElementTree.fromstring(data)
        r2=[]
        if root:            
            for child in root.findall('{http://www.sat.gob.mx/cfd/3}Complemento'):
                for pagos in child:
                    for pago in pagos:              
                        num_fac = float(pago.attrib['Monto'])
                        monto_fac = 0
                        monto_facto = 0                  
                        for inv in self.invoice_lines:
                            if inv.comision_col == False:
                                monto_fac += inv.allocation
                            else: 
                                print(monto_fac,"ddddrrrrrr",inv.allocation,inv.comision_cam)
                                monto_fac += inv.allocation - inv.comision_cam
                                monto_facto += inv.comision_cam
                        monto_fac_final = round(monto_fac,2)
                        monto_facto_final = round(monto_facto,2)
                        if num_fac == monto_fac_final:
                            values = {
                            'nodo': 1,
                            'FechaPago':pago.attrib['FechaPago'],
                            'FormaDePagoP':pago.attrib['FormaDePagoP'],
                            'MonedaP':pago.attrib['MonedaP'],
                            'Monto': pago.attrib['Monto'],                           
                            }
                            r2.append(values)
                        if num_fac == monto_facto_final:
                            values = {
                            'nodo': 2,
                            'FechaPago':pago.attrib['FechaPago'],
                            'FormaDePagoP':pago.attrib['FormaDePagoP'],
                            'MonedaP':pago.attrib['MonedaP'],
                            'Monto': pago.attrib['Monto'],                           
                            }
                            r2.append(values)
                            
            print("cccccccccccccc",r2)      
            return r2





class pagos_pagos(models.Model):
    _inherit = 'account.invoice'
    tipo_relacion = fields.Char(
        string='Tipo relacion',
    )
    uuid = fields.Char(
        string='UUID',
    )
    @api.multi
    def get_cfdi(self):
        print("sssssss")
        """To node CfdiRelacionados get documents related with each invoice
        from l10n_mx_edi_origin, hope the next structure:
            relation type|UUIDs separated by ,"""
        self.ensure_one()
        for rec in self:
            
            if rec.l10n_mx_edi_origin:
               
                origin = rec.l10n_mx_edi_origin.split('|')
                uuids = origin[1].split(',') if len(origin) > 1 else []
                print("ttttttttttttttttttttttt",origin[0])
                rec.write({'tipo_relacion':origin[0]})
                for u in uuids:
                    rec.write({'uuid':u})
                