# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class RepairProblemCategory(models.Model):
    _name = 'mobile.repair.problem.category'
    _description = 'Categoría de Problema de Reparación'
    _order = 'sequence, name'

    name = fields.Char('Nombre', required=True, translate=True, index=True)
    sequence = fields.Integer('Secuencia', default=10, index=True)
    color = fields.Integer('Color', default=1)
    active = fields.Boolean('Activo', default=True, index=True)
    problems_count = fields.Integer(
        'Cantidad de Problemas', 
        compute='_compute_problems_count',
        readonly=True
    )
    problem_ids = fields.One2many('mobile.repair.problem', 'category_id', string='Problemas')

    @api.depends('problem_ids', 'problem_ids.active')
    def _compute_problems_count(self):
        if not self.ids:
            for category in self:
                category.problems_count = 0
            return
        
        problem_data = self.env['mobile.repair.problem'].read_group(
            [('category_id', 'in', self.ids), ('active', '=', True)],
            ['category_id'],
            ['category_id']
        )
        mapped_data = {x['category_id'][0]: x['category_id_count'] for x in problem_data}
        for category in self:
            category.problems_count = mapped_data.get(category.id, 0)


class RepairProblem(models.Model):
    _name = 'mobile.repair.problem'
    _description = 'Problema de Reparación'
    _order = 'sequence, name'

    name = fields.Char('Nombre del Problema', required=True, translate=True, index=True)
    category_id = fields.Many2one(
        'mobile.repair.problem.category', 
        'Categoría', 
        required=True, 
        index=True,
        ondelete='restrict'
    )
    description = fields.Text('Descripción Detallada', translate=True)
    solution_template = fields.Text('Plantilla de Solución', translate=True)
    
    estimated_repair_time = fields.Float('Tiempo Estimado (horas)', default=1.0)
    estimated_cost = fields.Monetary('Costo Estimado', currency_field='currency_id')
    currency_id = fields.Many2one(
        'res.currency', 
        'Moneda',
        default=lambda self: self.env.company.currency_id,
        readonly=True
    )
    
    sequence = fields.Integer('Secuencia', default=10, index=True)
    active = fields.Boolean('Activo', default=True, index=True)
    display_name = fields.Char(
        string='Nombre Completo',
        compute='_compute_display_name',
        store=True,
        index=True,
        readonly=True
    )
    usage_count = fields.Integer(
        'Veces Usado',
        compute='_compute_usage_count',
        store=True,
        readonly=True
    )

    @api.depends('name', 'category_id.name')
    def _compute_display_name(self):
        for problem in self:
            if problem.category_id and problem.name:
                problem.display_name = f"{problem.category_id.name} / {problem.name}"
            else:
                problem.display_name = problem.name or _("Nuevo Problema")

    @api.depends('name')
    def _compute_usage_count(self):
        for problem in self:
            problem.usage_count = self.env['mobile.repair.order'].search_count([
                ('problem_ids', 'in', problem.id)
            ])

    def action_view_repair_orders(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': f'Reparaciones: {self.display_name}',
            'res_model': 'mobile.repair.order',
            'view_mode': 'kanban,list,form',
            'domain': [('problem_ids', 'in', self.ids)],
            'context': {
                'default_problem_ids': [(4, self.id)]
            }
        }

    _sql_constraints = [
        ('name_category_uniq', 'UNIQUE(name, category_id)', 
         'Ya existe un problema con este nombre en esta categoría'),
        ('positive_time', 'CHECK(estimated_repair_time >= 0)', 
         'El tiempo estimado debe ser positivo'),
        ('positive_cost', 'CHECK(estimated_cost >= 0)', 
         'El costo estimado debe ser positivo'),
    ]