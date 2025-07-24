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
        default='draft')
    boq_line = fields.One2many(
        comodel_name='sale.boq.line',
        inverse_name='boq_id',
        string="BoQ Lines",
        copy=True)
    amount_total = fields.Monetary(
        string="Total Amount",
        compute='_compute_amount_total',
        store=True,
        precompute=True,
        currency_field='currency_id')
    sale_order_id = fields.Many2one(
        comodel_name='sale.order',
        string="Generated Sale Order",
        readonly=True,
        copy=False)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', self.env._("New")) == self.env._("New"):
                vals['name'] = self.env['ir.sequence'].with_company(
                    vals.get('company_id')).next_by_code('sale.boq') or self.env._("New")

        return super().create(vals_list)

    def action_confirm(self):
        # Create sale order from BoQ
        if not self.sale_order_id:
            sale_order = self._create_sale_order()
            self.sale_order_id = sale_order.id
        self.write({'state': 'boq'})

    def _create_sale_order(self):
        """Create a sale order based on the BoQ lines"""
        # Prepare sale order values
        sale_order_vals = {
            'partner_id': self.partner_id.id,
            'company_id': self.company_id.id,
            'currency_id': self.currency_id.id,
            'origin': self.name,
            'note': f'Generated from BoQ: {self.name}',
        }

        # Create the sale order
        sale_orders = self.env['sale.order'].create([sale_order_vals])
        sale_order = sale_orders[0]

        # Create sale order lines from BoQ lines
        sale_line_vals_list = []
        for boq_line in self.boq_line:
            if boq_line.product_id:
                sale_line_vals = {
                    'order_id': sale_order.id,
                    'product_id': boq_line.product_id.id,
                    'name': boq_line.name,
                    'product_uom_qty': boq_line.product_uom_qty,
                    'product_uom': boq_line.product_uom.id if boq_line.product_uom else boq_line.product_id.uom_id.id,
                    'price_unit': boq_line.price_unit,
                    'force_invoiced_quantity': boq_line.product_uom_qty if not boq_line.is_invoicable else 0.0,
                }
                sale_line_vals_list.append(sale_line_vals)

        if sale_line_vals_list:
            self.env['sale.order.line'].create(sale_line_vals_list)

        return sale_order

    def action_view_sale_order(self):
        """Action to view the generated sale order"""
        if not self.sale_order_id:
            return

        return {
            'type': 'ir.actions.act_window',
            'name': 'Sale Order',
            'res_model': 'sale.order',
            'res_id': self.sale_order_id.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def action_cancel(self):
        self.write({'state': 'cancel'})

    def action_draft(self):
        self.write({'state': 'draft'})

    @api.depends('company_id')
    def _compute_currency_id(self):
        for boq in self:
            boq.currency_id = boq.company_id.currency_id

    @api.depends('boq_line.price_subtotal')
    def _compute_amount_total(self):
        for boq in self:
            boq.amount_total = sum(boq.boq_line.mapped('price_subtotal'))


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
    is_invoiceable = fields.Boolean(string="Invoiceable", default=True)
    name = fields.Text(
        string="Description",
        store=True, readonly=False, required=True)
    product_id = fields.Many2one(
        comodel_name='product.product',
        string="Product",
        change_default=True, ondelete='restrict', index='btree_not_null',
        domain="[('sale_ok', '=', True)]")
    product_uom = fields.Many2one(
        comodel_name='uom.uom',
        string="Unit of Measure",
        domain="[('category_id', '=', product_uom_category_id)]")
    product_uom_category_id = fields.Many2one(
        related='product_id.uom_id.category_id',
        readonly=True)
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

    @api.depends('product_uom_qty', 'price_unit')
    def _compute_amount(self):
        for line in self:
            line.price_subtotal = line.product_uom_qty * line.price_unit

    @api.onchange('product_id')
    def _onchange_product_id(self):
        if self.product_id:
            self.product_uom = self.product_id.uom_id
            self.name = self.product_id.name
            self.price_unit = self.product_id.list_price
