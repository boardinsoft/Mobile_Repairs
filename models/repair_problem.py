# -*- coding: utf-8 -*-

from odoo import models, fields, api

class RepairProblem(models.Model):
    """Catálogo de problemas comunes para acelerar el registro"""
    _name = 'mobile.repair.problem'
    _description = 'Catálogo de Problemas de Reparación'
    _order = 'sequence, name'
    
    name = fields.Char(
        string='Problema',
        required=True,
        help="Descripción del problema común"
    )
    
    description = fields.Text(
        string='Descripción Detallada',
        help="Descripción más específica del problema"
    )
    
    category_id = fields.Many2one(
        'mobile.repair.problem.category',
        string='Categoría',
        required=True,
        help="Categoría del problema para mejor organización"
    )
    
    estimated_repair_time = fields.Float(
        string='Tiempo Estimado (horas)',
        help="Tiempo estimado de reparación en horas"
    )
    
    estimated_cost = fields.Monetary(
        string='Costo Estimado',
        currency_field='currency_id',
        help="Costo estimado de la reparación"
    )
    
    currency_id = fields.Many2one(
        'res.currency',
        string='Moneda',
        default=lambda self: self.env.company.currency_id,
        required=True
    )
    
    solution_template = fields.Text(
        string='Plantilla de Solución',
        help="Plantilla de solución típica para este problema"
    )
    
    active = fields.Boolean(
        string='Activo',
        default=True
    )
    
    sequence = fields.Integer(
        string='Secuencia',
        default=10
    )
    
    usage_count = fields.Integer(
        string='Veces Usado',
        compute='_compute_usage_count',
        store=True
    )
    
    repair_orders_ids = fields.One2many(
        'mobile.repair.order',
        'problem_id',
        string='Órdenes de Reparación'
    )
    
    @api.depends('repair_orders_ids')
    def _compute_usage_count(self):
        """Cuenta cuántas veces se ha usado este problema"""
        for record in self:
            record.usage_count = len(record.repair_orders_ids)
    
    def name_get(self):
        """Personaliza el nombre mostrado"""
        result = []
        for record in self:
            name = record.name
            if record.category_id:
                name = f"[{record.category_id.name}] {name}"
            result.append((record.id, name))
        return result


class RepairProblemCategory(models.Model):
    """Categorías para organizar los problemas"""
    _name = 'mobile.repair.problem.category'
    _description = 'Categoría de Problemas de Reparación'
    _order = 'sequence, name'
    
    name = fields.Char(
        string='Categoría',
        required=True
    )
    
    color = fields.Integer(
        string='Color',
        help="Color para la categoría en las vistas kanban"
    )
    
    sequence = fields.Integer(
        string='Secuencia',
        default=10
    )
    
    active = fields.Boolean(
        string='Activo',
        default=True
    )
    
    problems_count = fields.Integer(
        string='Cantidad de Problemas',
        compute='_compute_problems_count'
    )
    
    problems_ids = fields.One2many(
        'mobile.repair.problem',
        'category_id',
        string='Problemas'
    )
    
    @api.depends('problems_ids')
    def _compute_problems_count(self):
        """Cuenta los problemas en esta categoría"""
        for record in self:
            record.problems_count = len(record.problems_ids.filtered('active'))