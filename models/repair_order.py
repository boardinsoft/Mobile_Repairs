# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import ValidationError, UserError
from datetime import datetime, timedelta

class RepairOrder(models.Model):
    """Modelo principal optimizado para órdenes de reparación móvil"""
    _name = 'mobile.repair.order'
    _description = 'Orden de Reparación Móvil'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'name'
    _order = 'priority desc, create_date desc'

    # ============================================================
    # CAMPOS PRINCIPALES (MINIMALISTA)
    # ============================================================
    
    name = fields.Char(
        string='Número',
        required=True,
        copy=False,
        readonly=True,
        index=True,
        default='Nuevo'
    )
    
    # Información básica
    customer_id = fields.Many2one(
        'res.partner',
        string='Cliente',
        required=True,
        tracking=True,
        index=True
    )
    
    device_id = fields.Many2one(
        'mobile_repair.device',
        string='Dispositivo',
        required=True,
        tracking=True,
        index=True,
        help="Seleccionar dispositivo registrado"
    )
    
    problem_id = fields.Many2one(
        'mobile.repair.problem',
        string='Problema Reportado',
        required=True,
        tracking=True,
        help="Seleccionar problema del catálogo"
    )
    
    problem_description = fields.Text(
        string='Detalles Adicionales',
        tracking=True,
        help="Información específica adicional sobre el problema"
    )
    
    # Estados simplificados
    state = fields.Selection([
        ('draft', 'Recibido'),
        ('in_progress', 'En Reparación'),
        ('ready', 'Listo'),
        ('delivered', 'Entregado'),
        ('cancelled', 'Cancelado'),
    ], string='Estado', default='draft', tracking=True, index=True)
    
    priority = fields.Selection([
        ('normal', 'Normal'),
        ('high', 'Alta'),
        ('urgent', 'Urgente')
    ], string='Prioridad', default='normal', tracking=True)
    
    # Asignación
    technician_id = fields.Many2one(
        'res.users',
        string='Técnico',
        domain=[('active', '=', True)],
        tracking=True,
        index=True
    )
    
    # Fechas clave
    date_received = fields.Datetime(
        string='Fecha Recepción',
        default=fields.Datetime.now,
        required=True,
        index=True
    )
    
    date_started = fields.Datetime(
        string='Inicio Reparación',
        readonly=True,
        tracking=True
    )
    
    date_completed = fields.Datetime(
        string='Reparación Completa',
        readonly=True,
        tracking=True
    )
    
    date_delivered = fields.Datetime(
        string='Fecha Entrega',
        readonly=True,
        tracking=True
    )
    
    # Líneas de presupuesto (servicios y repuestos)
    quote_line_ids = fields.One2many(
        'mobile.repair.quote.line',
        'repair_order_id',
        string='Líneas de Presupuesto',
        copy=True
    )
    
    currency_id = fields.Many2one(
        'res.currency',
        string='Moneda',
        default=lambda self: self.env.company.currency_id,
        required=True
    )
    
    # Integración con ventas y facturación
    sale_order_id = fields.Many2one(
        'sale.order',
        string='Orden de Venta',
        readonly=True,
        copy=False,
        tracking=True
    )
    
    invoice_id = fields.Many2one(
        'account.move',
        string='Factura',
        readonly=True,
        copy=False,
        tracking=True
    )
    
    invoice_state = fields.Selection(
        related='invoice_id.state',
        string='Estado Factura',
        readonly=True
    )
    
    invoiced = fields.Boolean(
        string='Facturado',
        compute='_compute_invoiced',
        store=True
    )
    
    total_amount = fields.Monetary(
        string='Importe Total',
        compute='_compute_total_amount',
        store=True,
        currency_field='currency_id'
    )
    
    # Información técnica
    diagnosis = fields.Text(
        string='Diagnóstico Técnico',
        help="Diagnóstico detallado del técnico"
    )
    
    solution_applied = fields.Text(
        string='Solución Aplicada',
        help="Descripción de la reparación realizada"
    )
    
    customer_notes = fields.Text(
        string='Notas del Cliente',
        help="Observaciones adicionales del cliente"
    )
    
    # Campos computados
    duration_days = fields.Float(
        string='Duración (días)',
        compute='_compute_duration',
        store=True
    )
    
    progress_percentage = fields.Integer(
        string='Progreso %',
        compute='_compute_progress',
        store=True
    )
    
    display_name = fields.Char(
        compute='_compute_display_name',
        store=True
    )
    
    # Campos relacionados del dispositivo
    device_brand = fields.Char(
        string='Marca',
        related='device_id.brand_id.name',
        store=True,
        readonly=True
    )
    
    device_model = fields.Char(
        string='Modelo',
        related='device_id.model_id.name',
        store=True,
        readonly=True
    )
    
    device_imei = fields.Char(
        string='IMEI',
        related='device_id.imei',
        store=True,
        readonly=True
    )
    
    device_physical_state = fields.Selection(
        string='Estado Físico del Dispositivo',
        related='device_id.physical_state',
        readonly=True
    )

    # ============================================================
    # MÉTODOS COMPUTADOS
    # ============================================================
    
    @api.depends('date_started', 'date_completed', 'date_received')
    def _compute_duration(self):
        """Calcula duración en días desde recepción hasta completado"""
        for record in self:
            if record.date_completed and record.date_received:
                delta = record.date_completed - record.date_received
                record.duration_days = delta.total_seconds() / 86400  # segundos a días
            else:
                record.duration_days = 0.0
    
    @api.depends('state', 'technician_id', 'diagnosis', 'solution_applied')
    def _compute_progress(self):
        """Calcula progreso automático basado en el estado y completitud"""
        for record in self:
            progress = 0
            
            if record.state == 'draft':
                progress = 10
            elif record.state == 'in_progress':
                progress = 30
                if record.diagnosis:
                    progress += 20
                if record.solution_applied:
                    progress += 30
            elif record.state == 'ready':
                progress = 90
            elif record.state == 'delivered':
                progress = 100
            elif record.state == 'cancelled':
                progress = 0
            
            # Bonificaciones
            if record.technician_id and record.state in ['in_progress', 'ready']:
                progress += 10
            
            record.progress_percentage = min(progress, 100)
    
    @api.depends('name', 'customer_id', 'device_id')
    def _compute_display_name(self):
        """Nombre de visualización mejorado"""
        for record in self:
            parts = [record.name]
            if record.customer_id:
                parts.append(record.customer_id.name)
            if record.device_id:
                device_name = record.device_id.display_name
                parts.append(device_name[:30] + '...' if len(device_name) > 30 else device_name)
            record.display_name = ' - '.join(parts)
    
    @api.depends('invoice_id')
    def _compute_invoiced(self):
        """Calcula si la orden está facturada"""
        for record in self:
            record.invoiced = bool(record.invoice_id and record.invoice_id.state == 'posted')
    
    @api.depends('quote_line_ids.subtotal')
    def _compute_total_amount(self):
        """Calcula el importe total basado en las líneas de presupuesto"""
        for record in self:
            record.total_amount = sum(record.quote_line_ids.mapped('subtotal'))

    # ============================================================
    # MÉTODOS DE NEGOCIO
    # ============================================================
    
    @api.model_create_multi
    def create(self, vals_list):
        """Asigna secuencia automática al crear"""
        for vals in vals_list:
            if vals.get('name', 'Nuevo') == 'Nuevo':
                vals['name'] = self.env['ir.sequence'].next_by_code('mobile.repair.order') or 'REP-ERROR'
        
        records = super().create(vals_list)
        
        # Actualizar estadísticas del dispositivo
        devices = records.mapped('device_id')
        if devices:
            devices._compute_repair_stats()
        
        return records
    
    def action_start_repair(self):
        """Inicia la reparación"""
        self.ensure_one()
        if self.state != 'draft':
            raise UserError("Solo se pueden iniciar reparaciones en estado 'Recibido'.")
        
        if not self.technician_id:
            raise UserError("Debe asignar un técnico antes de iniciar la reparación.")
        
        self.write({
            'state': 'in_progress',
            'date_started': fields.Datetime.now()
        })
        
        self.message_post(
            body=f"<b>Reparación iniciada</b><br/>Técnico: {self.technician_id.name}",
            message_type='notification'
        )
        return True
    
    def action_mark_ready(self):
        """Marca como lista para entrega"""
        self.ensure_one()
        if self.state != 'in_progress':
            raise UserError("Solo se pueden completar reparaciones en progreso.")
        
        if not self.solution_applied:
            raise UserError("Debe describir la solución aplicada antes de marcar como listo.")
        
        self.write({
            'state': 'ready',
            'date_completed': fields.Datetime.now()
        })
        
        self.message_post(
            body=f"<b>Reparación completada</b><br/>Duración: {self.duration_days:.1f} días",
            message_type='notification'
        )
        return True
    
    def action_deliver(self):
        """Entrega al cliente"""
        self.ensure_one()
        if self.state != 'ready':
            raise UserError("Solo se pueden entregar reparaciones que están listas.")
        
        self.write({
            'state': 'delivered',
            'date_delivered': fields.Datetime.now()
        })
        
        self.message_post(
            body="<b>Dispositivo entregado al cliente</b>",
            message_type='notification'
        )
        return True
    
    def action_cancel(self):
        """Cancela la orden"""
        self.ensure_one()
        if self.state == 'delivered':
            raise UserError("No se puede cancelar una orden ya entregada.")
        
        self.write({'state': 'cancelled'})
        self.message_post(
            body="<b>Orden cancelada</b>",
            message_type='notification'
        )
        return True
    
    def action_reset_to_draft(self):
        """Regresa a estado inicial"""
        self.ensure_one()
        self.write({
            'state': 'draft',
            'date_started': False,
            'date_completed': False,
            'date_delivered': False
        })
        return True
    
    def action_create_invoice(self):
        """Crear factura para la orden de reparación"""
        self.ensure_one()
        
        if self.invoice_id:
            raise UserError("Esta orden ya tiene una factura asociada.")
        
        if not self.total_amount:
            raise UserError("Debe establecer un costo estimado o final antes de facturar.")
        
        # Buscar o crear producto de servicio de reparación
        repair_product = self._get_or_create_repair_product()
        
        # Crear líneas de orden de venta desde las líneas de presupuesto
        order_lines = []
        for line in self.quote_line_ids:
            order_lines.append((0, 0, {
                'product_id': line.product_id.id,
                'name': line.description or line.product_id.name,
                'product_uom_qty': line.quantity,
                'price_unit': line.unit_price,
            }))
        
        # Si no hay líneas, usar producto de servicio genérico
        if not order_lines:
            order_lines.append((0, 0, {
                'product_id': repair_product.id,
                'name': f'Reparación {self.device_brand} {self.device_model} - {self.problem_id.name}',
                'product_uom_qty': 1,
                'price_unit': self.total_amount or 0.0,
            }))
        
        # Crear orden de venta
        sale_order_vals = {
            'partner_id': self.customer_id.id,
            'origin': self.name,
            'order_line': order_lines,
            'repair_order_id': self.id,
        }
        
        sale_order = self.env['sale.order'].create(sale_order_vals)
        self.sale_order_id = sale_order.id
        
        # Confirmar orden de venta y crear factura
        sale_order.action_confirm()
        
        # Crear factura desde la orden de venta
        invoice = sale_order._create_invoices()
        if invoice:
            self.invoice_id = invoice[0].id
            
            # Mensaje de seguimiento
            self.message_post(
                body=f"<b>Factura creada</b><br/>Número: {invoice[0].name}<br/>Importe: {self.total_amount} {self.currency_id.symbol}",
                message_type='notification'
            )
        
        return {
            'type': 'ir.actions.act_window',
            'name': 'Factura',
            'res_model': 'account.move',
            'res_id': self.invoice_id.id,
            'view_mode': 'form',
            'target': 'current'
        }
    
    def action_view_invoice(self):
        """Ver factura asociada"""
        self.ensure_one()
        if not self.invoice_id:
            raise UserError("Esta orden no tiene factura asociada.")
        
        return {
            'type': 'ir.actions.act_window',
            'name': 'Factura',
            'res_model': 'account.move',
            'res_id': self.invoice_id.id,
            'view_mode': 'form',
            'target': 'current'
        }
    
    def action_view_sale_order(self):
        """Ver orden de venta asociada"""
        self.ensure_one()
        if not self.sale_order_id:
            raise UserError("Esta orden no tiene orden de venta asociada.")
        
        return {
            'type': 'ir.actions.act_window',
            'name': 'Orden de Venta',
            'res_model': 'sale.order',
            'res_id': self.sale_order_id.id,
            'view_mode': 'form',
            'target': 'current'
        }
    
    def _get_or_create_repair_product(self):
        """Obtiene un producto de servicio de reparación desde el módulo de inventario"""
        # Buscar productos de servicio que puedan ser usados para reparaciones
        repair_products = self.env['product.product'].search([
            ('type', '=', 'service'),
            ('sale_ok', '=', True),
            ('active', '=', True)
        ], limit=1)
        
        if not repair_products:
            # Crear un producto de servicio básico si no existe ninguno
            repair_products = self.env['product.product'].create({
                'name': 'Servicio de Reparación Móvil',
                'type': 'service',
                'sale_ok': True,
                'purchase_ok': False,
                'list_price': 0.0,
                'invoice_policy': 'order',
                'categ_id': self.env.ref('product.product_category_all').id,
            })
        
        return repair_products
    
    def action_create_device(self):
        """Crear dispositivo rápidamente"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Crear Dispositivo',
            'res_model': 'mobile_repair.device',
            'view_mode': 'form',
            'context': {
                'default_imei': '',
                'repair_order_id': self.id
            },
            'target': 'new'
        }

    # ============================================================
    # VALIDACIONES
    # ============================================================
    
    @api.constrains('quote_line_ids')
    def _check_quote_lines(self):
        """Valida las líneas de presupuesto"""
        for record in self:
            for line in record.quote_line_ids:
                if line.quantity <= 0:
                    raise ValidationError("La cantidad debe ser mayor a cero.")
                if line.unit_price < 0:
                    raise ValidationError("El precio unitario no puede ser negativo.")
    
    @api.constrains('date_received', 'date_started', 'date_completed')
    def _check_dates(self):
        """Valida secuencia lógica de fechas"""
        for record in self:
            if record.date_started and record.date_started < record.date_received:
                raise ValidationError("La fecha de inicio no puede ser anterior a la recepción.")
            
            if record.date_completed and record.date_started and record.date_completed < record.date_started:
                raise ValidationError("La fecha de completado no puede ser anterior al inicio.")

    # ============================================================
    # MÉTODOS DE UTILIDAD
    # ============================================================
    
    def name_get(self):
        """Personaliza el nombre mostrado"""
        result = []
        for record in self:
            name = f"{record.name}"
            if record.customer_id:
                name += f" - {record.customer_id.name}"
            result.append((record.id, name))
        return result


# ============================================================
# EXTENSIÓN DEL MODELO DE CLIENTES PARA DISPOSITIVOS
# ============================================================

class ResPartner(models.Model):
    """Extensión del modelo de clientes para mostrar estadísticas de reparaciones"""
    _inherit = 'res.partner'
    customer_rank = fields.Integer(string='Customer Rank', default=0)
    repair_orders_count = fields.Integer(
        string='Órdenes de Reparación',
        compute='_compute_repair_stats'
    )
    
    repair_orders_completed = fields.Integer(
        string='Reparaciones Completadas',
        compute='_compute_repair_stats'
    )
    
    repair_orders_pending = fields.Integer(
        string='Reparaciones Pendientes',
        compute='_compute_repair_stats'
    )
    
    last_repair_date = fields.Datetime(
        string='Última Reparación',
        compute='_compute_repair_stats'
    )
    
    def _compute_repair_stats(self):
        """Calcula estadísticas de reparaciones del cliente"""
        for partner in self:
            if not partner.customer_rank:
                partner.repair_orders_count = 0
                partner.repair_orders_completed = 0
                partner.repair_orders_pending = 0
                partner.last_repair_date = False
                continue
            
            RepairOrder = self.env['mobile.repair.order']
            
            # Total de órdenes
            partner.repair_orders_count = RepairOrder.search_count([
                ('customer_id', '=', partner.id)
            ])
            
            # Completadas
            partner.repair_orders_completed = RepairOrder.search_count([
                ('customer_id', '=', partner.id),
                ('state', 'in', ['ready', 'delivered'])
            ])
            
            # Pendientes
            partner.repair_orders_pending = RepairOrder.search_count([
                ('customer_id', '=', partner.id),
                ('state', 'in', ['draft', 'in_progress'])
            ])
            
            # Última reparación
            last_order = RepairOrder.search([
                ('customer_id', '=', partner.id)
            ], order='date_received desc', limit=1)
            
            partner.last_repair_date = last_order.date_received if last_order else False
    
    def action_view_customer_repairs(self):
        """Acción para ver las reparaciones del cliente"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': f'Reparaciones - {self.name}',
            'res_model': 'mobile.repair.order',
            'view_mode': 'list,kanban,form',
            'domain': [('customer_id', '=', self.id)],
            'context': {
                'search_default_group_by_state': 1,
                'default_customer_id': self.id
            }
        }


# ============================================================
# MODELO DE LÍNEAS DE PRESUPUESTO
# ============================================================

class RepairQuoteLine(models.Model):
    """Líneas de presupuesto para servicios y repuestos"""
    _name = 'mobile.repair.quote.line'
    _description = 'Línea de Presupuesto de Reparación'
    _order = 'sequence, id'
    
    repair_order_id = fields.Many2one(
        'mobile.repair.order',
        string='Orden de Reparación',
        required=True,
        ondelete='cascade',
        index=True
    )
    
    sequence = fields.Integer(
        string='Secuencia',
        default=10
    )
    
    product_id = fields.Many2one(
        'product.product',
        string='Producto/Servicio',
        required=True,
        domain=[('sale_ok', '=', True)],
        change_default=True
    )
    
    description = fields.Text(
        string='Descripción',
        required=True
    )
    
    quantity = fields.Float(
        string='Cantidad',
        digits='Product Unit of Measure',
        required=True,
        default=1.0
    )
    
    unit_price = fields.Monetary(
        string='Precio Unitario',
        currency_field='currency_id',
        required=True
    )
    
    subtotal = fields.Monetary(
        string='Subtotal',
        currency_field='currency_id',
        compute='_compute_subtotal',
        store=True
    )
    
    currency_id = fields.Many2one(
        related='repair_order_id.currency_id',
        store=True,
        readonly=True
    )
    
    product_type = fields.Selection(
        related='product_id.type',
        readonly=True
    )
    
    @api.depends('quantity', 'unit_price')
    def _compute_subtotal(self):
        """Calcula el subtotal de la línea"""
        for line in self:
            line.subtotal = line.quantity * line.unit_price
    
    @api.onchange('product_id')
    def _onchange_product_id(self):
        """Actualiza descripción y precio al cambiar producto"""
        if self.product_id:
            self.description = self.product_id.name
            self.unit_price = self.product_id.list_price
    
    def name_get(self):
        """Personaliza el nombre mostrado"""
        result = []
        for line in self:
            name = f"{line.product_id.name} x {line.quantity}"
            result.append((line.id, name))
        return result


# ============================================================
# EXTENSIÓN DEL MODELO DE ÓRDENES DE VENTA
# ============================================================

class SaleOrder(models.Model):
    """Extensión del modelo de órdenes de venta para vincular con reparaciones"""
    _inherit = 'sale.order'
    
    repair_order_id = fields.Many2one(
        'mobile.repair.order',
        string='Orden de Reparación',
        readonly=True,
        copy=False
    )
    
    is_repair_order = fields.Boolean(
        string='Es Orden de Reparación',
        compute='_compute_is_repair_order',
        store=True
    )
    
    @api.depends('repair_order_id')
    def _compute_is_repair_order(self):
        """Marca si la orden de venta proviene de una reparación"""
        for order in self:
            order.is_repair_order = bool(order.repair_order_id)
    
    def action_view_repair_order(self):
        """Ver orden de reparación asociada"""
        self.ensure_one()
        if not self.repair_order_id:
            raise UserError("Esta orden de venta no tiene orden de reparación asociada.")
        
        return {
            'type': 'ir.actions.act_window',
            'name': 'Orden de Reparación',
            'res_model': 'mobile.repair.order',
            'res_id': self.repair_order_id.id,
            'view_mode': 'form',
            'target': 'current'
        }