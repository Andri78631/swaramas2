# -*- coding: utf-8 -*-

# from odoo import models, fields, api


# class bmd_demo_swaramas(models.Model):
#     _name = 'bmd_demo_swaramas.bmd_demo_swaramas'
#     _description = 'bmd_demo_swaramas.bmd_demo_swaramas'

#     name = fields.Char()
#     value = fields.Integer()
#     value2 = fields.Float(compute="_value_pc", store=True)
#     description = fields.Text()
#
#     @api.depends('value')
#     def _value_pc(self):
#         for record in self:
#             record.value2 = float(record.value) / 100

