# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import ValidationError, UserError

class RepairQuoteLine(models.Model):
    """Línea de presupuesto para una orden de reparación. Puede ser un producto o un servicio."""
    _name = 'mobile.repair.quote.line'
    _description = 'Línea de Presupuesto de Reparación'
    _order = 'sequence, id'
    
    repair_order_id = fields.Many2one('mobile.repair.order', string='Orden de Reparación', required=True, ondelete='cascade')
    sequence = fields.Integer(string='Secuencia', default=10)
    
    display_type = fields.Selection([
        ('line_section', 'Sección'), 
        ('line_note', 'Nota')],
        default=False, help="Permite añadir secciones o notas en el presupuesto."
    )
    
    product_id = fields.Many2one('product.product', string='Producto/Servicio', domain=[('sale_ok', '=', True)], change_default=True)
    name = fields.Text(string='Descripción', required=True)
    quantity = fields.Float(string='Cantidad', digits='Product Unit of Measure', default=1.0)
    product_uom = fields.Many2one('uom.uom', string='Unidad de Medida', domain="[('category_id', '=', product_uom_category_id)]")
    product_uom_category_id = fields.Many2one(related='product_id.uom_id.category_id')
    
    price_unit = fields.Float(string='Precio Unitario', digits='Product Price')
    discount = fields.Float(string='Descuento (%)', digits='Discount', default=0.0)
    tax_id = fields.Many2many('account.tax', string='Impuestos', domain=['|', ('active', '=', False), ('active', '=', True)])
    
    price_subtotal = fields.Monetary(string='Subtotal', currency_field='currency_id', compute='_compute_amount', store=True)
    price_total = fields.Monetary(string='Total', currency_field='currency_id', compute='_compute_amount', store=True)
    currency_id = fields.Many2one(related='repair_order_id.currency_id', store=True)

    @api.depends('quantity', 'discount', 'price_unit', 'tax_id')
    def _compute_amount(self):
        """Calcula los importes de la línea, aplicando descuentos e impuestos."""
        for line in self:
            if line.display_type:
                line.price_subtotal = line.price_total = 0.0
                continue
            
            price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
            taxes = line.tax_id.compute_all(
                price,
                line.repair_order_id.currency_id,
                line.quantity,
                product=line.product_id,
                partner=line.repair_order_id.customer_id
            )
            line.update({'price_subtotal': taxes['total_excluded'], 'price_total': taxes['total_included']})

    @api.onchange('product_id')
    def _onchange_product_id(self):
        """Autocompleta los datos de la línea al seleccionar un producto."""
        if not self.product_id:
            return
        self.name = self.product_id.get_product_multiline_description_sale()
        self.price_unit = self.product_id.list_price
        self.product_uom = self.product_id.uom_id
        self.tax_id = self.product_id.taxes_id.filtered(lambda t: t.company_id == self.env.company)

class RepairOrder(models.Model):
    """Gestiona el flujo completo de una orden de reparación."""
    _name = 'mobile.repair.order'
    _description = 'Orden de Reparación Móvil'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'priority desc, create_date desc'

    def _get_default_currency_id(self):
        return self.env.company.currency_id.id

    name = fields.Char(string='Número', required=True, copy=False, readonly=True, index=True, default='Nuevo')
    customer_id = fields.Many2one('res.partner', string='Cliente', required=True, tracking=True, index=True)
    device_id = fields.Many2one('mobile_repair.device', string='Dispositivo', required=True, tracking=True, index=True)
    problem_id = fields.Many2one('mobile.repair.problem', string='Problema Reportado', required=True, tracking=True)
    problem_description = fields.Text(string='Detalles Adicionales', tracking=True)
    state = fields.Selection([
        ('draft', 'Recibido'), ('in_progress', 'En Reparación'), ('ready', 'Listo'),
        ('delivered', 'Entregado'), ('cancelled', 'Cancelado')],
        string='Estado', default='draft', tracking=True, index=True
    )
    priority = fields.Selection([('normal', 'Normal'), ('high', 'Alta'), ('urgent', 'Urgente')], string='Prioridad', default='normal', tracking=True)
    technician_id = fields.Many2one('res.users', string='Técnico', domain=[('active', '=', True)], tracking=True, index=True)
    
    diagnosis = fields.Text(string='Diagnóstico Técnico', tracking=True)
    solution_applied = fields.Text(string='Solución Aplicada', tracking=True)

    date_received = fields.Datetime(string='Fecha Recepción', default=fields.Datetime.now, required=True, index=True)
    date_started = fields.Datetime(string='Inicio Reparación', readonly=True, tracking=True)
    date_completed = fields.Datetime(string='Reparación Completa', readonly=True, tracking=True)
    date_delivered = fields.Datetime(string='Fecha Entrega', readonly=True, tracking=True)

    quote_line_ids = fields.One2many('mobile.repair.quote.line', 'repair_order_id', string='Líneas de Presupuesto', copy=True)
    
    device_info = fields.Char(string='Información del Dispositivo', compute='_compute_device_info', store=True)
    currency_id = fields.Many2one('res.currency', string='Moneda', default=_get_default_currency_id, required=True)
    company_id = fields.Many2one('res.company', string='Compañía', default=lambda self: self.env.company, required=True)
    
    amount_untaxed = fields.Monetary(string='Base Imponible', compute='_compute_amounts', store=True)
    amount_tax = fields.Monetary(string='Impuestos', compute='_compute_amounts', store=True)
    amount_total = fields.Monetary(string='Importe Total', compute='_compute_amounts', store=True)
    tax_totals = fields.Json(string="Resumen de Impuestos", compute='_compute_tax_totals')

    location_id = fields.Many2one(
        'stock.location', string='Ubicación de Repuestos', domain=[('usage', '=', 'internal')], required=True,
        check_company=True, default=lambda self: self.env['stock.warehouse'].search([('company_id', '=', self.env.company.id)], limit=1).lot_stock_id
    )
    stock_picking_id = fields.Many2one('stock.picking', string='Transferencia de Stock', readonly=True, copy=False)
    picking_count = fields.Integer(string="Transferencias", compute='_compute_picking_count')
    
    sale_order_id = fields.Many2one('sale.order', string='Orden de Venta', readonly=True, copy=False, tracking=True)
    invoice_id = fields.Many2one('account.move', string='Factura', compute='_compute_invoice_id', store=True, readonly=True, copy=False)
    invoiced = fields.Boolean(string='Facturado', compute='_compute_invoiced', store=True, help="Indica si la factura asociada ha sido pagada.")

    # --- MÉTODOS DE CÓMPUTO ---
    def _compute_picking_count(self):
        for order in self:
            order.picking_count = 1 if order.stock_picking_id else 0

    @api.depends('quote_line_ids.price_total')
    def _compute_amounts(self):
        for order in self:
            amount_untaxed = sum(order.quote_line_ids.mapped('price_subtotal'))
            amount_total = sum(order.quote_line_ids.mapped('price_total'))
            order.update({'amount_untaxed': amount_untaxed, 'amount_tax': amount_total - amount_untaxed, 'amount_total': amount_total})

    @api.depends('quote_line_ids.price_subtotal', 'customer_id', 'currency_id')
    def _compute_tax_totals(self):
        for order in self:
            base_lines = []
            for line in order.quote_line_ids.filtered(lambda l: not l.display_type):
                base_lines.append(self.env['account.tax']._prepare_base_line_for_taxes_computation(
                    line, **{'tax_ids': line.tax_id, 'price_unit': line.price_unit, 'quantity': line.quantity,
                             'discount': line.discount, 'currency_id': order.currency_id, 'product_id': line.product_id,
                             'partner_id': order.customer_id}))
            self.env['account.tax']._add_tax_details_in_base_lines(base_lines, order.company_id)
            self.env['account.tax']._round_base_lines_tax_details(base_lines, order.company_id)
            order.tax_totals = self.env['account.tax']._get_tax_totals_summary(base_lines, order.currency_id, order.company_id)
    
    @api.depends('sale_order_id.invoice_ids')
    def _compute_invoice_id(self):
        for order in self:
            order.invoice_id = order.sale_order_id.invoice_ids and order.sale_order_id.invoice_ids[0] or False
    
    @api.depends('invoice_id.payment_state')
    def _compute_invoiced(self):
        for order in self:
            order.invoiced = order.invoice_id and order.invoice_id.payment_state in ('paid', 'in_payment')

    @api.depends('device_id')
    def _compute_device_info(self):
        for record in self:
            record.device_info = record.device_id.display_name if record.device_id else "Sin dispositivo"

    # --- MÉTODOS DE ACCIÓN (BOTONES) ---
    def action_start_repair(self):
        self.ensure_one()
        if not self.technician_id:
            raise UserError("Debe asignar un técnico antes de iniciar la reparación.")
        if not self.stock_picking_id: self._create_stock_picking()
        self.write({'state': 'in_progress', 'date_started': fields.Datetime.now()})
        return True

    def action_mark_ready(self):
        self.ensure_one()
        if self.stock_picking_id and self.stock_picking_id.state == 'assigned':
            self.stock_picking_id.button_validate()
        self.write({'state': 'ready', 'date_completed': fields.Datetime.now()})
        return True
        
    def action_deliver(self):
        self.ensure_one()
        self.write({'state': 'delivered', 'date_delivered': fields.Datetime.now()})
        return True

    def action_cancel(self):
        if self.stock_picking_id: self.stock_picking_id.action_cancel()
        return super().action_cancel()
        
    def _create_stock_picking(self):
        self.ensure_one()
        picking_type = self.env['stock.picking.type'].search([
            ('code', '=', 'outgoing'), ('warehouse_id.company_id', '=', self.company_id.id)], limit=1)
        if not picking_type: raise UserError("No se encontró un tipo de albarán de 'Salidas' para su almacén.")
        storable_lines = self.quote_line_ids.filtered(lambda l: not l.display_type and l.product_id.type == 'product')
        if not storable_lines: return
        
        picking = self.env['stock.picking'].create({
            'partner_id': self.customer_id.id, 'picking_type_id': picking_type.id,
            'location_id': self.location_id.id, 'location_dest_id': self.env.ref('stock.stock_location_customers').id,
            'origin': self.name, 'company_id': self.company_id.id,
            'move_ids': [(0, 0, {'name': line.product_id.name, 'product_id': line.product_id.id,
                                 'product_uom_qty': line.quantity, 'product_uom': line.product_uom.id,
                                 'location_id': self.location_id.id, 'location_dest_id': self.env.ref('stock.stock_location_customers').id})
                         for line in storable_lines],
        })
        picking.action_confirm()
        picking.action_assign()
        self.stock_picking_id = picking.id
        return picking

    def action_view_stock_picking(self):
        self.ensure_one()
        return {'type': 'ir.actions.act_window', 'name': 'Transferencia de Stock',
                'res_model': 'stock.picking', 'res_id': self.stock_picking_id.id, 'view_mode': 'form', 'target': 'current'}

    def action_create_invoice(self):
        self.ensure_one()
        if not self.amount_total: raise UserError("No se puede crear una factura con importe total cero.")
        sale_order = self.env['sale.order'].create({
            'partner_id': self.customer_id.id, 'origin': self.name, 'repair_order_id': self.id,
            'order_line': [(0, 0, {'product_id': line.product_id.id, 'name': line.name,
                                   'product_uom_qty': line.quantity, 'price_unit': line.price_unit,
                                   'discount': line.discount, 'tax_id': [(6, 0, line.tax_id.ids)]})
                           for line in self.quote_line_ids.filtered(lambda l: not l.display_type)],
        })
        self.sale_order_id = sale_order.id
        return {'type': 'ir.actions.act_window', 'name': 'Orden de Venta',
                'res_model': 'sale.order', 'res_id': sale_order.id, 'view_mode': 'form', 'target': 'current'}

    # --- CORRECCIÓN: Métodos para los botones inteligentes que fueron eliminados ---
    def action_view_sale_order(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Orden de Venta',
            'res_model': 'sale.order',
            'res_id': self.sale_order_id.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def action_view_invoice(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Factura',
            'res_model': 'account.move',
            'res_id': self.invoice_id.id,
            'view_mode': 'form',
            'target': 'current',
        }

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'Nuevo') == 'Nuevo':
                vals['name'] = self.env['ir.sequence'].next_by_code('mobile.repair.order') or 'Nuevo'
        return super().create(vals_list)

class SaleOrder(models.Model):
    _inherit = 'sale.order'
    repair_order_id = fields.Many2one('mobile.repair.order', string='Orden de Reparación', readonly=True, copy=False)

class ResPartner(models.Model):
    _inherit = 'res.partner'
    repair_orders_count = fields.Integer(string='Órdenes de Reparación', compute='_compute_repair_orders_count')
    
    def _compute_repair_orders_count(self):
        """Calcula el número de reparaciones por cliente de forma optimizada."""
        if not self.ids:
            self.repair_orders_count = 0
            return
        repair_data = self.env['mobile.repair.order'].read_group(
            [('customer_id', 'in', self.ids)],
            ['customer_id'],
            ['customer_id']
        )
        count_map = {item['customer_id'][0]: item['customer_id_count'] for item in repair_data}
        for partner in self:
            partner.repair_orders_count = count_map.get(partner.id, 0)