# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import ValidationError, UserError

class RepairOrderLine(models.Model):
    """Línea de presupuesto para una orden de reparación. Puede ser un producto o un servicio."""
    _name = 'mobile.repair.order.line'
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
    product_uom_qty = fields.Float(string='Cantidad', digits='Product Unit of Measure', default=1.0)
    product_uom = fields.Many2one('uom.uom', string='Unidad de Medida', domain="[('category_id', '=', product_uom_category_id)]")
    product_uom_category_id = fields.Many2one(related='product_id.uom_id.category_id')
    
    price_unit = fields.Float(string='Precio Unitario', digits='Product Price')
    discount = fields.Float(string='Descuento (%)', digits='Discount', default=0.0)
    tax_id = fields.Many2many('account.tax', string='Impuestos', domain=['|', ('active', '=', False), ('active', '=', True)])
    
    currency_id = fields.Many2one(related='repair_order_id.currency_id', store=True, readonly=True, depends=['repair_order_id.currency_id'])
    price_subtotal = fields.Monetary(string='Subtotal', currency_field='currency_id', compute='_compute_amount', store=True)
    price_total = fields.Monetary(string='Total', currency_field='currency_id', compute='_compute_amount', store=True)

    @api.depends('product_uom_qty', 'discount', 'price_unit', 'tax_id')
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
                line.product_uom_qty,
                product=line.product_id,
                partner=line.repair_order_id.partner_id
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

    _sql_constraints = [
        ('name_uniq', 'UNIQUE(name)', 'El número de orden debe ser único'),
        ('positive_amount', 'CHECK(amount_total >= 0)', 'El importe total no puede ser negativo'),
    ]

    @api.depends_context('company')
    def _get_default_currency_id(self):
        return self.env.company.currency_id.id

    name = fields.Char(string='Número', required=True, copy=False, readonly=True, index=True, default='Nuevo')
    partner_id = fields.Many2one('res.partner', string='Cliente', required=True, tracking=True, index=True, ondelete='restrict')
    device_id = fields.Many2one('mobile.repair.device', string='Dispositivo', required=True, tracking=True, index=True, ondelete='restrict')
    partner_phone = fields.Char(related='partner_id.phone', string='Teléfono', readonly=True, store=True, index=True)
    partner_email = fields.Char(related='partner_id.email', string='Email', readonly=True, store=True, index=True)
    problem_ids = fields.Many2many('mobile.repair.problem', 'mobile_repair_problem_order_rel', 'order_id', 'problem_id', string='Problemas Reportados', required=True, tracking=True)
    device_condition = fields.Text(string='Condición del Dispositivo')
    accessories_included = fields.Text(string='Accesorios Incluidos')
    internal_notes = fields.Text(string='Notas Internas')
    date_start = fields.Datetime(string='Fecha de Inicio', tracking=True)
    date_finished = fields.Datetime(string='Fecha de Finalización', tracking=True)
    date_promised = fields.Datetime(string='Fecha Prometida', tracking=True, index=True)
    problem_description = fields.Text(string='Detalles Adicionales', tracking=True)
    
    # ESTADOS CORREGIDOS según requerimientos
    state = fields.Selection([
        ('draft', 'Borrador'),
        ('in_repair', 'En reparación'), 
        ('repaired', 'Reparado'),
        ('delivered', 'Entregado'),
        ('cancelled', 'Cancelado')
    ], string='Estado', default='draft', tracking=True, index=True)
    
    priority = fields.Selection([('normal', 'Normal'), ('high', 'Alta'), ('urgent', 'Urgente')], string='Prioridad', default='normal', tracking=True)
    color = fields.Integer(string='Color', default=0)
    technician_id = fields.Many2one('res.users', string='Técnico', domain=[('active', '=', True)], tracking=True, index=True, ondelete='set null')
    
    diagnosis = fields.Text(string='Diagnóstico Técnico', tracking=True)
    solution_applied = fields.Text(string='Solución Aplicada', tracking=True)

    date_received = fields.Datetime(string='Fecha Recepción', default=fields.Datetime.now, required=True, index=True)
    date_started = fields.Datetime(string='Inicio Reparación', readonly=True, tracking=True)
    date_completed = fields.Datetime(string='Reparación Completa', readonly=True, tracking=True)
    date_delivered = fields.Datetime(string='Fecha Entrega', readonly=True, tracking=True)

    # Líneas de presupuesto heredadas de ventas
    order_line = fields.One2many('mobile.repair.order.line', 'repair_order_id', string='Líneas de Presupuesto', copy=True)
    
    device_info = fields.Char(string='Información del Dispositivo', compute='_compute_device_info', store=True, precompute=True)
    currency_id = fields.Many2one('res.currency', string='Moneda', default=_get_default_currency_id, required=True)
    company_id = fields.Many2one('res.company', string='Compañía', default=lambda self: self.env.company, required=True)
    
    amount_untaxed = fields.Monetary(string='Base Imponible', compute='_compute_amounts', store=True, readonly=True)
    amount_tax = fields.Monetary(string='Impuestos', compute='_compute_amounts', store=True, readonly=True)
    amount_total = fields.Monetary(string='Importe Total', compute='_compute_amounts', store=True, readonly=True)

    location_id = fields.Many2one(
        'stock.location', string='Ubicación de Repuestos', domain=[('usage', '=', 'internal')], required=True,
        check_company=True, default=lambda self: self.env['stock.warehouse'].search([('company_id', '=', self.env.company.id)], limit=1).lot_stock_id
    )
    stock_picking_id = fields.Many2one('stock.picking', string='Transferencia de Stock', readonly=True, copy=False)
    picking_count = fields.Integer(string="Transferencias", compute='_compute_picking_count')
    
    sale_order_id = fields.Many2one('sale.order', string='Orden de Venta', readonly=True, copy=False, tracking=True)
    invoice_id = fields.Many2one('account.move', string='Factura', compute='_compute_invoice_id', store=True, readonly=True, copy=False)
    invoiced = fields.Boolean(string='Facturado', compute='_compute_invoiced', store=True, help="Indica si la factura asociada ha sido pagada.", index=True)

    problem_count = fields.Integer(string="Problem Count", compute='_compute_problem_count', store=True)
    progress_percentage = fields.Integer(string="Progress Percentage", compute='_compute_progress_percentage', store=True)
    technician_image = fields.Binary(related='technician_id.image_128', string="Technician Avatar", readonly=True)

    # --- MÉTODOS DE CÓMPUTO ---

    @api.depends('problem_ids')
    def _compute_problem_count(self):
        for order in self:
            order.problem_count = len(order.problem_ids)

    @api.depends('state')
    def _compute_progress_percentage(self):
        for order in self:
            if order.state == 'draft':
                order.progress_percentage = 0
            elif order.state == 'in_repair':
                order.progress_percentage = 50
            elif order.state == 'repaired':
                order.progress_percentage = 75
            elif order.state == 'delivered':
                order.progress_percentage = 100
            else:
                order.progress_percentage = 0

    @api.constrains('date_promised', 'date_received')
    def _check_dates(self):
        for order in self:
            if order.date_promised and order.date_promised < order.date_received:
                raise ValidationError('La fecha prometida no puede ser anterior a la fecha de recepción')

    def _compute_picking_count(self):
        for order in self:
            order.picking_count = 1 if order.stock_picking_id else 0

    @api.depends('order_line.price_total')
    def _compute_amounts(self):
        for order in self:
            order_lines = order.order_line
            order.amount_untaxed = sum(order_lines.mapped('price_subtotal'))
            order.amount_total = sum(order_lines.mapped('price_total'))
            order.amount_tax = order.amount_total - order.amount_untaxed
    
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
            if record.device_id:
                record.device_info = record.device_id.display_name
            else:
                record.device_info = "Sin dispositivo"

    # --- MÉTODOS DE ACCIÓN CORREGIDOS PARA NUEVOS ESTADOS ---
    def action_start_repair(self):
        """Inicia la reparación (draft -> in_repair)"""
        self.ensure_one()
        if not self.technician_id:
            raise UserError("Debe asignar un técnico antes de iniciar la reparación.")
        if not self.stock_picking_id: 
            self._create_stock_picking()
        self.write({'state': 'in_repair', 'date_started': fields.Datetime.now()})
        return True

    def action_mark_repaired(self):
        """Marca como reparado (in_repair -> repaired)"""
        self.ensure_one()
        if self.stock_picking_id and self.stock_picking_id.state == 'assigned':
            self.stock_picking_id.button_validate()
        self.write({'state': 'repaired', 'date_completed': fields.Datetime.now()})
        return True
    
    def action_deliver(self):
        """Entrega el dispositivo (repaired -> delivered)"""
        self.ensure_one()
        self.write({'state': 'delivered', 'date_delivered': fields.Datetime.now()})
        return True

    def action_cancel(self):
        """Cancela la orden"""
        if self.stock_picking_id: 
            self.stock_picking_id.action_cancel()
        self.write({'state': 'cancelled'})
        return True
    
    def action_reset_to_draft(self):
        """Regresa a borrador"""
        self.ensure_one()
        self.write({'state': 'draft'})
        return True
    
    def _create_stock_picking(self):
        self.ensure_one()
        picking_type = self.env['stock.picking.type'].search([
            ('code', '=', 'outgoing'), ('warehouse_id.company_id', '=', self.company_id.id)], limit=1)
        if not picking_type: 
            raise UserError("No se encontró un tipo de albarán de 'Salidas' para su almacén.")
        
        storable_lines = self.order_line.filtered(lambda l: not l.display_type and l.product_id.type == 'product')
        if not storable_lines: 
            return
        
        picking = self.env['stock.picking'].create({
            'partner_id': self.partner_id.id, 
            'picking_type_id': picking_type.id,
            'location_id': self.location_id.id, 
            'location_dest_id': self.env.ref('stock.stock_location_customers').id,
            'origin': self.name, 
            'company_id': self.company_id.id,
            'move_ids': [(0, 0, {
                'name': line.product_id.name, 
                'product_id': line.product_id.id,
                'product_uom_qty': line.product_uom_qty, 
                'product_uom': line.product_uom.id,
                'location_id': self.location_id.id, 
                'location_dest_id': self.env.ref('stock.stock_location_customers').id
            }) for line in storable_lines],
        })
        picking.action_confirm()
        picking.action_assign()
        self.stock_picking_id = picking.id
        return picking

    def action_view_stock_picking(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window', 
            'name': 'Transferencia de Stock',
            'res_model': 'stock.picking', 
            'res_id': self.stock_picking_id.id, 
            'view_mode': 'form', 
            'target': 'current'
        }

    def action_create_invoice(self):
        self.ensure_one()
        if not self.order_line:
            raise UserError("No hay líneas para facturar.")
        
        invoice_vals = self._prepare_invoice()
        invoice = self.env['account.move'].create(invoice_vals)
        invoice.action_post()
        
        self.invoice_id = invoice
        
        return {
            'type': 'ir.actions.act_window',
            'name': 'Factura',
            'res_model': 'account.move',
            'res_id': invoice.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def _prepare_invoice(self):
        return {
            'move_type': 'out_invoice',
            'partner_id': self.partner_id.id,
            'currency_id': self.currency_id.id,
            'ref': self.name,
            'invoice_origin': self.name,
            'invoice_line_ids': [(0, 0, self._prepare_invoice_line(line)) 
                                 for line in self.order_line.filtered(lambda l: not l.display_type)],
        }

    def _prepare_invoice_line(self, line):
        return {
            'product_id': line.product_id.id,
            'name': line.name,
            'quantity': line.product_uom_qty,
            'price_unit': line.price_unit,
            'discount': line.discount,
            'tax_ids': [(6, 0, line.tax_id.ids)],
        }

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

    def unlink(self):
        for order in self:
            if order.state != 'cancelled':
                raise UserError("No se puede eliminar una orden de reparación que no esté en estado 'Cancelado'.")
        return super().unlink()

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
            [('partner_id', 'in', self.ids)],
            ['partner_id'],
            ['partner_id']
        )
        count_map = {item['partner_id'][0]: item['partner_id_count'] for item in repair_data}
        for partner in self:
            partner.repair_orders_count = count_map.get(partner.id, 0)