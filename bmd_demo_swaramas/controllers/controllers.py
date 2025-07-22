# -*- coding: utf-8 -*-
# from odoo import http


# class BmdDemoSwaramas(http.Controller):
#     @http.route('/bmd_demo_swaramas/bmd_demo_swaramas', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/bmd_demo_swaramas/bmd_demo_swaramas/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('bmd_demo_swaramas.listing', {
#             'root': '/bmd_demo_swaramas/bmd_demo_swaramas',
#             'objects': http.request.env['bmd_demo_swaramas.bmd_demo_swaramas'].search([]),
#         })

#     @http.route('/bmd_demo_swaramas/bmd_demo_swaramas/objects/<model("bmd_demo_swaramas.bmd_demo_swaramas"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('bmd_demo_swaramas.object', {
#             'object': obj
#         })

