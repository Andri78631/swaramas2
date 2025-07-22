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
    currency_id = fields.Many2one(
        comodel_name='res.currency',
        compute='_compute_currency_id',
        store=True,
        precompute=True,
        ondelete='restrict'
    )
    partner_id = fields.Many2one(comodel_name="res.partner", string="Customer",
                                 required=True, ondelete="restrict", index=True)
    state = fields.Selection(
        selection=SALE_BOQ_STATE,
        string="Status",
        readonly=True, copy=False, index=True,
        tracking=3,
        default='draft')
    boq_line = fields.One2many(
        comodel_name='sale.boq.line',
        inverse_name='boq_id',
        string="BoQ Lines",
        copy=True)

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

    @api.depends('company_id')
    def _compute_currency_id(self):
        for boq in self:
            boq.currency_id = boq.company_id.currency_id


class SaleBoQLine(models.Model):
    _name = 'sale.boq.line'
    _description = 'BoQ Line'

    boq_id = fields.Many2one(
        comodel_name='sale.boq',
        string="BoQ Reference",
        required=True, ondelete='cascade', index=True, copy=False)
    currency_id = fields.Many2one(
        related='boq_id.currency_id',
        depends=['boq_id.currency_id'],
        store=True, precompute=True)
    name = fields.Text(
        string="Description",
        store=True, readonly=False, required=True)
    product_id = fields.Many2one(
        comodel_name='product.product',
        string="Product",
        change_default=True, ondelete='restrict', index='btree_not_null',
        domain="[('sale_ok', '=', True)]")
    product_uom_qty = fields.Float(
        string="Quantity",
        digits='Product Unit of Measure', default=1.0,
        store=True, readonly=False, required=True)
    price_unit = fields.Float(
        string="Unit Price",
        digits='Product Price',
        store=True, readonly=False, required=True)
    price_subtotal = fields.Monetary(
        string="Subtotal",
        compute='_compute_amount',
        store=True, precompute=True)

    def _compute_amount(self):
        for line in self:
            line.price_subtotal = line.product_uom_qty * line.price_unit
