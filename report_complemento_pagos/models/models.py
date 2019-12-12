# -*- coding: utf-8 -*-

from odoo import models, fields, api
import base64
import tempfile
import os
from xml.etree import ElementTree

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
            
            if rec.carga_lineas == 0:
                rec.complemento()
                rec.write({'carga_lineas':1})

            

    @api.multi
    def complemento(self):
        self.complemento_ids = [(5, 0, 0)]
        data = base64.decodestring(self.l10n_mx_edi_cfdi)
        root =ElementTree.fromstring(data)
        print ("roooooooooooooooooooooooooooot",root)
        count = 0
        if count == 0:
            count += count + 1
            for child in root.findall('{http://www.sat.gob.mx/cfd/3}Complemento'):         
                for pagos in child:
                    for pago in pagos:
                        for doc in pago:
                            fpp = pago.get('FormaDePagoP')
                            if fpp:
                                if pago.attrib['FormaDePagoP'] == '17':
                                    self.complemento_ids.create({
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
                                    })
                                       
                                else:
                                    self.complemento_ids.create({
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
                                    })
                                       
                                   
                            else:
                                print("pago normal")
