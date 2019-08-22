# -*- coding: utf-8 -*-
from odoo import http

# class ReportComplementoPagos(http.Controller):
#     @http.route('/report_complemento_pagos/report_complemento_pagos/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/report_complemento_pagos/report_complemento_pagos/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('report_complemento_pagos.listing', {
#             'root': '/report_complemento_pagos/report_complemento_pagos',
#             'objects': http.request.env['report_complemento_pagos.report_complemento_pagos'].search([]),
#         })

#     @http.route('/report_complemento_pagos/report_complemento_pagos/objects/<model("report_complemento_pagos.report_complemento_pagos"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('report_complemento_pagos.object', {
#             'object': obj
#         })