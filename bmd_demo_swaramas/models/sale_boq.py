from odoo import api, fields, models

SALE_BOQ_STATE = [
    ('draft', "Draft"),
    ('boq', "BoQ"),
    ('cancel', "Cancelled"),
]


class SaleBoQ(models.Model):
    _name = 'sale.boq'
    _description = 'BoQ'

    name = fields.Char(
        string="BoQ Reference",
        required=True, copy=False, readonly=False,
        index='trigram',
        default=lambda self: self.env._('New'))
    company_id = fields.Many2one(
        comodel_name='res.company',
        required=True, index=True,
        default=lambda self: self.env.company)
    partner_id = fields.Many2one(comodel_name="res.partner", string="Customer",
                                 required=True, ondelete="restrict", index=True)
    state = fields.Selection(
        selection=SALE_BOQ_STATE,
        string="Status",
        readonly=True, copy=False, index=True,
        tracking=3,
        default='draft')
    # date_expired = fields.Date(string="Expiration Date", required=False)
    # date_quotation = fields.Datetime(string="Quotation Date", required=False)
    # pricelist_id = fields.Many2one(comodel_name="product.pricelist", string="Pricelist", required=False, ondelete="restrict", index=True)
    # payment_term_id = fields.Many2one(comodel_name="account.payment.term", string="Payment Terms", required=False, ondelete="restrict", index=True)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', self.env._("New")) == self.env._("New"):
                vals['name'] = self.env['ir.sequence'].with_company(
                    vals.get('company_id')).next_by_code('sale.boq') or self.env._("New")

        return super().create(vals_list)

    def action_confirm(self):
        self.write({'state': 'boq'})

    def action_cancel(self):
        self.write({'state': 'cancel'})
