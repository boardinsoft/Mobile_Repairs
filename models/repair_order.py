# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import ValidationError, UserError
from datetime import datetime, timedelta

class RepairOrder(models.Model):
    _name = 'mobile.repair.order'
    _description = 'Repair Order'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'name'
    _order = 'priority desc, repair_date desc, id desc'  # ✅ Priorizar urgentes

    # ✅ SECUENCIA SIMPLIFICADA Y ROBUSTA
    name = fields.Char(
        string='Referencia', 
        required=True, 
        copy=False, 
        readonly=True, 
        index=True, 
        default='Nueva Orden'  # ✅ Simplificado
    )
    
    # ✅ INFORMACIÓN BÁSICA MEJORADA
    customer_id = fields.Many2one(
        'res.partner', 
        string='Cliente', 
        required=True, 
        index=True,
        tracking=True,  # ✅ Seguimiento en chatter
        help="Cliente propietario del dispositivo"
    )
    
    device_id = fields.Many2one(
        'mobile.device', 
        string='Dispositivo', 
        required=True,
        tracking=True,  # ✅ Seguimiento en chatter
        help="Dispositivo a reparar"
    )
    
    # ✅ ESTADOS SIMPLIFICADOS
    status = fields.Selection([
        ('draft', 'Recibido'),  # ✅ Más claro que "Borrador"
        ('in_progress', 'En Reparación'),  # ✅ Más específico
        ('completed', 'Listo para Entrega'),  # ✅ Más claro
        ('delivered', 'Entregado'),  # ✅ Nuevo estado
        ('canceled', 'Cancelado'),
    ], 
        string='Estado', 
        default='draft', 
        tracking=True,
        help="Estado actual de la reparación"
    )
    
    # ✅ PRIORIDAD VISUAL MEJORADA
    priority = fields.Selection([
        ('low', 'Baja'),
        ('normal', 'Normal'),
        ('high', 'Alta'),
        ('urgent', 'Urgente')
    ], 
        string='Prioridad', 
        default='normal',
        tracking=True,
        help="Prioridad de la reparación"
    )
    
    # ✅ CAMPOS DE TIEMPO OPTIMIZADOS
    repair_date = fields.Datetime(
        string='Fecha de Recepción', 
        default=fields.Datetime.now,
        required=True,
        tracking=True,
        help="Cuándo se recibió el dispositivo"
    )
    
    start_date = fields.Datetime(
        string='Inicio de Reparación',
        readonly=True,
        tracking=True,
        help="Cuándo se inició la reparación"
    )
    
    completion_date = fields.Datetime(
        string='Reparación Completada',
        readonly=True,
        tracking=True,
        help="Cuándo se completó la reparación"
    )
    
    delivery_date = fields.Datetime(
        string='Fecha de Entrega',
        readonly=True,
        tracking=True,
        help="Cuándo se entregó al cliente"
    )
    
    # ✅ TÉCNICO CON DOMINIO SIMPLIFICADO (para evitar errores de grupo)
    technician_id = fields.Many2one(
        'res.users', 
        string='Técnico',
        # Dominio simplificado para evitar errores
        domain=[('active', '=', True)],
        tracking=True,
        help="Técnico asignado a la reparación"
    )
    
    # ✅ TIPO DE FALLA OBLIGATORIO
    failure_type_id = fields.Many2one(
        'mobile.fault',
        string='Tipo de Falla Principal',
        required=True,  # ✅ Ahora obligatorio
        tracking=True,
        help="Falla principal reportada"
    )
    
    # ✅ PROGRESO AUTOMÁTICO MEJORADO
    progress = fields.Float(
        string='Progreso (%)',
        compute='_compute_progress',
        store=True,  # ✅ Almacenar para búsquedas
        help="Progreso automático de la reparación"
    )
    
    # ✅ DURACIÓN MEJORADA
    duration_hours = fields.Float(
        string='Tiempo de Reparación (Horas)',
        compute='_compute_duration_hours',
        store=True,
        help="Duración real de la reparación"
    )
    
    # ✅ CAMPOS FINANCIEROS
    estimated_cost = fields.Monetary(
        string='Presupuesto',
        currency_field='currency_id',
        tracking=True,
        help="Presupuesto inicial estimado"
    )
    
    total_amount = fields.Monetary(
        string='Total Final', 
        compute='_compute_total_amount', 
        store=True, 
        currency_field='currency_id',
        help="Costo total real de la reparación"
    )
    
    # ✅ CAMPOS DE FACTURACIÓN
    invoice_id = fields.Many2one(
        'account.move',
        string='Factura',
        readonly=True,
        tracking=True,
        help="Factura asociada a esta orden de reparación"
    )
    
    invoice_count = fields.Integer(
        string='Número de Facturas',
        compute='_compute_invoice_count',
        help="Número de facturas asociadas"
    )
    
    # ✅ OTROS CAMPOS IMPORTANTES
    description = fields.Text(
        string='Problema Reportado',
        help="Descripción del problema según el cliente"
    )
    
    notes = fields.Text(
        string='Notas del Técnico',
        help="Notas internas del técnico durante la reparación"
    )
    
    customer_notes = fields.Text(
        string='Observaciones del Cliente',
        help="Información adicional proporcionada por el cliente"
    )
    
    # ✅ RELACIONES
    repair_line_ids = fields.One2many(
        'mobile.repair.line', 
        'order_id', 
        string='Repuestos y Servicios',
        help="Productos y servicios utilizados"
    )
    
    currency_id = fields.Many2one(
        'res.currency', 
        string='Moneda', 
        default=lambda self: self.env.company.currency_id,
        required=True
    )

    # ✅ MÉTODOS COMPUTADOS OPTIMIZADOS
    @api.depends('start_date', 'completion_date')
    def _compute_duration_hours(self):
        """Calcula duración real de reparación (sin contar recepción)"""
        for record in self:
            if record.start_date and record.completion_date:
                delta = record.completion_date - record.start_date
                record.duration_hours = round(delta.total_seconds() / 3600, 2)
            else:
                record.duration_hours = 0.0

    @api.depends('status', 'repair_line_ids', 'technician_id', 'failure_type_id')
    def _compute_progress(self):
        """Progreso automático más inteligente"""
        for record in self:
            progress = 0
            
            # Estado base
            if record.status == 'draft':
                progress = 5  # Solo recibido
            elif record.status == 'in_progress':
                progress = 25  # Iniciado
            elif record.status == 'completed':
                progress = 85  # Listo
            elif record.status == 'delivered':
                progress = 100  # Terminado
            elif record.status == 'canceled':
                progress = 0
            
            # Bonificaciones por completitud (solo si no está terminado)
            if record.status not in ['delivered', 'canceled']:
                if record.technician_id:
                    progress += 10
                if record.failure_type_id:
                    progress += 5
                if record.repair_line_ids:
                    progress += 15
                if record.estimated_cost > 0:
                    progress += 5
            
            record.progress = min(progress, 100)

    @api.depends('repair_line_ids.price_subtotal')
    def _compute_total_amount(self):
        """Cálculo de total"""
        for order in self:
            order.total_amount = sum(line.price_subtotal for line in order.repair_line_ids)

    @api.depends('invoice_id')
    def _compute_invoice_count(self):
        """Calcular el número de facturas"""
        for record in self:
            record.invoice_count = 1 if record.invoice_id else 0

    # ✅ SECUENCIA AUTOMÁTICA MEJORADA
    @api.model_create_multi
    def create(self, vals_list):
        """Secuencia automática simplificada"""
        for vals in vals_list:
            if vals.get('name', 'Nueva Orden') == 'Nueva Orden':
                # Crear secuencia si no existe
                sequence = self.env['ir.sequence'].search([('code', '=', 'mobile.repair.order')], limit=1)
                if not sequence:
                    sequence = self.env['ir.sequence'].create({
                        'name': 'Secuencia Orden de Reparación',
                        'code': 'mobile.repair.order',
                        'prefix': 'REP',
                        'padding': 5,
                        'number_next': 1,
                        'number_increment': 1,
                    })
                
                vals['name'] = sequence.next_by_id() or 'REP-ERROR'
        return super().create(vals_list)

    # ✅ ACCIONES MEJORADAS CON VALIDACIONES INTELIGENTES
    def action_start_repair(self):
        """Iniciar reparación con validaciones"""
        for record in self:
            if record.status != 'draft':
                raise UserError("Solo se pueden iniciar reparaciones recibidas.")
            
            if not record.technician_id:
                raise UserError("Debe asignar un técnico antes de iniciar.")
            
            if not record.failure_type_id:
                raise UserError("Debe especificar el tipo de falla antes de iniciar.")
            
            record.write({
                'status': 'in_progress',
                'start_date': fields.Datetime.now()
            })
            
            record.message_post(
                body=f"🔧 <b>Reparación iniciada</b><br/>"
                     f"Técnico: {record.technician_id.name}<br/>"
                     f"Falla: {record.failure_type_id.name}",
                message_type='notification'
            )

    def action_complete(self):
        """Completar reparación"""
        for record in self:
            if record.status != 'in_progress':
                raise UserError("Solo se pueden completar reparaciones en progreso.")
            
            if not record.repair_line_ids:
                # ✅ Warning en lugar de error crítico
                record.message_post(
                    body="⚠️ <b>Atención:</b> Se completó sin líneas de reparación.",
                    message_type='notification'
                )
            
            record.write({
                'status': 'completed',
                'completion_date': fields.Datetime.now()
            })
            
            record.message_post(
                body=f"✅ <b>Reparación completada</b><br/>"
                     f"Duración: {record.duration_hours:.1f} horas<br/>"
                     f"Total: {record.currency_id.symbol}{record.total_amount:,.2f}",
                message_type='notification'
            )

    def action_deliver(self):
        """Nueva acción: Entregar al cliente"""
        for record in self:
            if record.status != 'completed':
                raise UserError("Solo se pueden entregar reparaciones completadas.")
            
            record.write({
                'status': 'delivered',
                'delivery_date': fields.Datetime.now()
            })
            
            record.message_post(
                body="📦 <b>Dispositivo entregado al cliente</b>",
                message_type='notification'
            )

    def action_cancel(self):
        """Cancelar orden de reparación"""
        for record in self:
            if record.status in ['delivered', 'canceled']:
                raise UserError("No se puede cancelar una orden entregada o ya cancelada.")
            
            if record.invoice_id:
                raise UserError("No se puede cancelar una orden que ya tiene factura. Cancele primero la factura.")
            
            record.write({'status': 'canceled'})
            record.message_post(
                body="❌ <b>Orden de reparación cancelada</b>",
                message_type='notification'
            )

    def action_reset_to_draft(self):
        """Regresar a borrador"""
        for record in self:
            if record.status == 'draft':
                raise UserError("La orden ya está en estado borrador.")
            
            if record.invoice_id:
                raise UserError("No se puede regresar a borrador una orden que tiene factura.")
            
            record.write({
                'status': 'draft',
                'start_date': False,
                'completion_date': False,
                'delivery_date': False
            })
            
            record.message_post(
                body="🔄 <b>Orden regresada a borrador</b>",
                message_type='notification'
            )

    # ✅ MÉTODOS DE FACTURACIÓN RÁPIDA
    def action_create_invoice(self):
        """Crear factura para la orden de reparación - MÉTODO RÁPIDO"""
        self.ensure_one()
        
        # ✅ Validaciones previas
        if self.status != 'completed':
            raise UserError("Solo se pueden facturar órdenes completadas.")
            
        if self.invoice_id:
            raise UserError("Esta orden ya tiene una factura asociada.")
            
        if not self.repair_line_ids:
            raise UserError("La orden debe tener al menos una línea de reparación para facturar.")

        # ✅ Buscar diario de ventas
        journal = self.env['account.journal'].search([
            ('type', '=', 'sale'),
            ('company_id', '=', self.env.company.id)
        ], limit=1)
        
        if not journal:
            raise UserError("No se encontró un diario de ventas configurado.")

        # ✅ Crear la factura con datos optimizados
        invoice_vals = self._prepare_invoice_values(journal)
        invoice = self.env['account.move'].create(invoice_vals)
        
        # ✅ Crear líneas de factura
        self._create_invoice_lines(invoice)
        
        # ✅ Asociar factura con la orden
        self.invoice_id = invoice.id
        
        # ✅ Mensaje de éxito con información útil
        self.message_post(
            body=f"💰 <b>Factura creada</b><br/>"
                 f"Número: {invoice.name}<br/>"
                 f"Total: {self.currency_id.symbol}{self.total_amount:,.2f}<br/>"
                 f"Cliente: {self.customer_id.name}",
            message_type='notification'
        )
        
        # ✅ Retornar acción para mostrar la factura inmediatamente
        return {
            'type': 'ir.actions.act_window',
            'name': f'Factura - {self.name}',
            'res_model': 'account.move',
            'res_id': invoice.id,
            'view_mode': 'form',
            'target': 'current',
            'context': {'create': False}  # Evitar crear nueva factura accidentalmente
        }

    def _prepare_invoice_values(self, journal):
        """Preparar valores para crear la factura"""
        self.ensure_one()
        
        return {
            'move_type': 'out_invoice',
            'partner_id': self.customer_id.id,
            'invoice_date': fields.Date.today(),
            'journal_id': journal.id,
            'payment_term_id': self.customer_id.property_payment_term_id.id if self.customer_id.property_payment_term_id else False,
            'invoice_origin': self.name,
            'currency_id': self.currency_id.id,
            'ref': f'Reparación {self.name} - {self.device_id.display_name or "Dispositivo"}',
            'narration': f'Reparación de {self.device_id.display_name or "dispositivo"}\n'
                        f'Problema: {self.failure_type_id.name}\n'
                        f'Técnico: {self.technician_id.name or "No asignado"}'
        }

    def _create_invoice_lines(self, invoice):
        """Crear líneas de factura basadas en las líneas de reparación"""
        self.ensure_one()
        
        for line in self.repair_line_ids:
            # ✅ Obtener cuenta contable
            account = self._get_invoice_line_account(line)
            
            # ✅ Preparar valores de la línea
            invoice_line_vals = {
                'move_id': invoice.id,
                'product_id': line.product_id.id if line.product_id else False,
                'name': self._format_invoice_line_description(line),
                'quantity': line.quantity,
                'product_uom_id': line.product_uom_id.id if line.product_uom_id else False,
                'price_unit': line.price_unit,
                'account_id': account,
            }
            
            # ✅ Aplicar impuestos automáticamente
            if line.product_id and line.product_id.taxes_id:
                invoice_line_vals['tax_ids'] = [(6, 0, line.product_id.taxes_id.ids)]
            
            # ✅ Crear línea de factura
            self.env['account.move.line'].create(invoice_line_vals)

    def _format_invoice_line_description(self, repair_line):
        """Formatear descripción de línea de factura"""
        if repair_line.description:
            return repair_line.description
        elif repair_line.product_id:
            return repair_line.product_id.display_name
        else:
            return 'Servicio de Reparación'

    def _get_invoice_line_account(self, repair_line):
        """Obtener cuenta contable para línea de factura - INTELIGENTE"""
        account = False
        
        # ✅ 1. Intentar cuenta del producto
        if repair_line.product_id:
            account = repair_line.product_id.property_account_income_id
            if not account:
                account = repair_line.product_id.categ_id.property_account_income_categ_id
        
        # ✅ 2. Buscar cuenta por defecto de ingresos
        if not account:
            account = self.env['account.account'].search([
                ('company_id', '=', self.env.company.id),
                ('account_type', 'in', ['income', 'income_other']),
            ], limit=1)
        
        # ✅ 3. Última opción: cuenta de ventas general
        if not account:
            account = self.env['account.account'].search([
                ('company_id', '=', self.env.company.id),
                ('code', '=like', '70%'),
            ], limit=1)
        
        # ✅ Error descriptivo si no se encuentra cuenta
        if not account:
            product_name = repair_line.product_id.display_name if repair_line.product_id else repair_line.description
            raise UserError(
                f"No se pudo determinar la cuenta contable para: {product_name}\n\n"
                f"Soluciones:\n"
                f"• Configure una cuenta de ingresos en el producto\n"
                f"• Configure una cuenta de ingresos en la categoría del producto\n"
                f"• Verifique que exista un plan contable válido"
            )
        
        return account.id

    def action_view_invoice(self):
        """Ver la factura asociada"""
        self.ensure_one()
        
        if not self.invoice_id:
            raise UserError("Esta orden no tiene una factura asociada.")
        
        return {
            'type': 'ir.actions.act_window',
            'name': f'Factura - {self.name}',
            'res_model': 'account.move',
            'res_id': self.invoice_id.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def action_quick_invoice_and_deliver(self):
        """ACCIÓN SÚPER RÁPIDA: Facturar y marcar como entregado"""
        self.ensure_one()
        
        # ✅ Crear factura
        invoice_action = self.action_create_invoice()
        
        # ✅ Marcar como entregado automáticamente
        self.action_deliver()
        
        # ✅ Mensaje de éxito completo
        self.message_post(
            body=f"🚀 <b>Proceso completo</b><br/>"
                 f"✅ Factura creada: {self.invoice_id.name}<br/>"
                 f"✅ Dispositivo marcado como entregado<br/>"
                 f"💰 Total: {self.currency_id.symbol}{self.total_amount:,.2f}",
            message_type='notification'
        )
        
        return invoice_action

    # ✅ VALIDACIONES SIMPLIFICADAS
    @api.constrains('estimated_cost')
    def _check_estimated_cost(self):
        for record in self:
            if record.estimated_cost < 0:
                raise ValidationError("El presupuesto no puede ser negativo.")

    @api.constrains('repair_date')
    def _check_repair_date(self):
        for record in self:
            if record.repair_date > fields.Datetime.now():
                # ✅ Solo advertencia, no error
                record.message_post(
                    body="⚠️ La fecha de recepción está en el futuro. Verifique si es correcto.",
                    message_type='notification'
                )

    def name_get(self):
        """Nombre con información útil"""
        result = []
        for record in self:
            name = f"{record.name}"
            if record.customer_id:
                name += f" - {record.customer_id.name}"
            if record.device_id:
                brand = record.device_id.brand_id.name if record.device_id.brand_id else ""
                model = record.device_id.model_id.name if record.device_id.model_id else ""
                if brand or model:
                    name += f" ({brand} {model})".strip()
            result.append((record.id, name))
        return result