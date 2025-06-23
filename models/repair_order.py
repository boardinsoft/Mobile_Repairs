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
    
    problem_description = fields.Text(
        string='Problema Reportado',
        required=True,
        tracking=True
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
    
    # Información financiera
    estimated_cost = fields.Monetary(
        string='Presupuesto',
        currency_field='currency_id',
        tracking=True
    )
    
    final_cost = fields.Monetary(
        string='Costo Final',
        currency_field='currency_id',
        tracking=True
    )
    
    currency_id = fields.Many2one(
        'res.currency',
        string='Moneda',
        default=lambda self: self.env.company.currency_id,
        required=True
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
    
    @api.constrains('estimated_cost', 'final_cost')
    def _check_costs(self):
        """Valida que los costos no sean negativos"""
        for record in self:
            if record.estimated_cost < 0 or record.final_cost < 0:
                raise ValidationError("Los costos no pueden ser negativos.")
    
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