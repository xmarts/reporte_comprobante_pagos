# -*- coding: utf-8 -*-

from odoo import models, fields, api

class pagos_pagos(models.Model):
    _inherit = 'account.payment'

    @api.model
    def l10n_mx_edi_get_pago_etree(self, cfdi):
        if not hasattr(cfdi, 'Complemento'):
            return None
        attribute = 'pago10:Pagos[1]'
        namespace = {'pago10': 'http://www.sat.gob.mx/Pagos'}
        node = cfdi.Complemento.xpath(attribute, namespaces=namespace)
        return node[0] if node else None