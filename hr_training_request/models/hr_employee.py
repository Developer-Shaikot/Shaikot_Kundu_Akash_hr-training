# -*- coding: utf-8 -*-
"""
hr.employee extension — adds training_request_count computed field and
the smart button action to open related training requests.

Uses read_group() for the compute to avoid N+1 queries (NFR-PERF-01).
Record rules on hr.training.request are automatically applied to the
read_group() call — no sudo() needed here.
"""

from odoo import api, fields, models, _


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    training_request_count = fields.Integer(
        string='Training Requests',
        compute='_compute_training_request_count',
        help='Number of training requests submitted by this employee.',
    )

    def _compute_training_request_count(self):
        """
        Compute the count of training requests per employee using a single
        SQL GROUP BY query (read_group) to avoid N+1 queries.

        Record rules on hr.training.request are applied automatically by
        the ORM for the current user — no sudo() required or used here.
        This means an employee sees only their own count, a manager sees
        their team's count, and HR sees all.
        """
        TrainingRequest = self.env['hr.training.request']
        data = TrainingRequest.read_group(
            domain=[('employee_id', 'in', self.ids)],
            fields=['employee_id'],
            groupby=['employee_id'],
        )
        count_map = {d['employee_id'][0]: d['employee_id_count'] for d in data}
        for employee in self:
            employee.training_request_count = count_map.get(employee.id, 0)

    def action_open_training_requests(self):
        """
        Open the list of training requests for this specific employee.
        The viewer's record rules are applied automatically — an employee
        can only open their own, a manager sees their reports' records, etc.
        """
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Training Requests — %s') % self.name,
            'res_model': 'hr.training.request',
            'view_mode': 'list,form',
            'domain': [('employee_id', '=', self.id)],
            'context': {
                'default_employee_id': self.id,
                'search_default_employee_id': self.id,
            },
        }
