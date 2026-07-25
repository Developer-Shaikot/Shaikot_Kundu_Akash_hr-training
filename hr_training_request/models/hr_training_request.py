# -*- coding: utf-8 -*-
"""
hr.training.request — Primary business model.

Implements the training request lifecycle with a guarded Finite State Machine:
    draft → submitted → manager_approved → hr_approved
                   ↘ rejected ↗                ↘ rejected
    (cancelled from draft or submitted by owner)

Security is enforced at FOUR independent layers:
  Layer 1 (DB):     ir.rule domain filters (see security/ir_rules.xml)
  Layer 2 (ORM):    ir.model.access.csv + field-level groups= on hr_notes
  Layer 3 (Python): action_*() guard methods — TRUE enforcement for all channels
  Layer 4 (UI):     XML attrs/groups — UX convenience only, NOT enforcement
"""

from odoo import api, fields, models, _
from odoo.exceptions import AccessError, UserError, ValidationError


class HrTrainingRequest(models.Model):
    _name = 'hr.training.request'
    _description = 'HR Training Request'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc, id desc'
    _rec_name = 'course_name'

    # ─────────────────────────────────────────────
    # Fields
    # ─────────────────────────────────────────────

    employee_id = fields.Many2one(
        comodel_name='hr.employee',
        string='Employee',
        required=True,
        tracking=True,
        default=lambda self: self.env.user.employee_id,
        help='The employee submitting this training request.',
    )

    manager_id = fields.Many2one(
        comodel_name='hr.employee',
        string='Line Manager',
        related='employee_id.parent_id',
        store=True,
        readonly=True,
        help='Auto-populated from the employee\'s line manager (parent_id).',
    )

    course_name = fields.Char(
        string='Course / Certification',
        required=True,
        tracking=True,
        help='Name of the training course or certification being requested.',
    )

    training_provider = fields.Char(
        string='Training Provider',
        help='External institution or provider delivering the training.',
    )

    start_date = fields.Date(
        string='Start Date',
        tracking=True,
    )

    end_date = fields.Date(
        string='End Date',
        tracking=True,
    )

    cost = fields.Float(
        string='Estimated Cost',
        digits=(10, 2),
        tracking=True,
        help='Estimated or actual cost of the training (in company currency).',
    )

    justification = fields.Text(
        string='Justification',
        help='Employee\'s written rationale for this training request.',
    )

    state = fields.Selection(
        selection=[
            ('draft', 'Draft'),
            ('submitted', 'Submitted'),
            ('manager_approved', 'Manager Approved'),
            ('hr_approved', 'HR Approved'),
            ('rejected', 'Rejected'),
            ('cancelled', 'Cancelled'),
        ],
        string='Status',
        default='draft',
        required=True,
        tracking=True,
        copy=False,
        help='Current lifecycle state of the training request.',
    )

    hr_notes = fields.Text(
        string='HR Notes',
        tracking=True,
        # Field-level group restriction (Layer 2 enforcement):
        # ORM excludes this field from fields_get(), strips it from RPC
        # responses, and raises AccessError on direct read/write by non-HR users.
        groups='hr_training_request.group_training_hr',
        help='Internal HR notes — only visible and editable by HR Approvers.',
    )

    # ─────────────────────────────────────────────
    # Constraints
    # ─────────────────────────────────────────────

    @api.constrains('start_date', 'end_date')
    def _check_dates(self):
        """Validate that end_date is strictly after start_date."""
        for rec in self:
            if rec.start_date and rec.end_date:
                if rec.end_date <= rec.start_date:
                    raise ValidationError(_(
                        'The end date must be after the start date. '
                        '(Start: %s — End: %s)'
                    ) % (rec.start_date, rec.end_date))

    @api.constrains('cost')
    def _check_cost(self):
        """Validate that cost is not negative."""
        for rec in self:
            if rec.cost is not None and rec.cost < 0:
                raise ValidationError(_(
                    'Training cost cannot be a negative value. '
                    'Please enter 0 or a positive amount.'
                ))

    # ─────────────────────────────────────────────
    # Helper: group membership checks
    # ─────────────────────────────────────────────

    def _is_manager_approver(self):
        """Return True if the current user belongs to the Manager Approver group."""
        return self.env.user.has_group('hr_training_request.group_training_manager')

    def _is_hr_approver(self):
        """Return True if the current user belongs to the HR Approver group."""
        return self.env.user.has_group('hr_training_request.group_training_hr')

    def _is_record_manager(self, rec):
        """
        Return True if the current user is the line manager of the employee
        on the given record. Used as an additional actor check for the manager
        approval stage (complements group membership check).
        """
        return (
            rec.manager_id and
            rec.manager_id.user_id and
            rec.manager_id.user_id == self.env.user
        )

    # ─────────────────────────────────────────────
    # State Transition Methods (Layer 3 enforcement)
    # Each method follows the four-step guard pattern:
    #   1. State pre-condition check
    #   2. Actor authorization check
    #   3. Business rule validation
    #   4. State transition execution
    # ─────────────────────────────────────────────

    def action_submit(self):
        """
        Transition: draft → submitted
        Actor:      Request owner (employee whose employee_id matches current user)
        Guards:     state == 'draft', owner check, end_date > start_date, cost >= 0
        """
        for rec in self:
            # Step 1: State pre-condition
            if rec.state != 'draft':
                raise UserError(_(
                    'Only draft requests can be submitted. '
                    'Current status: %s'
                ) % dict(rec._fields['state'].selection).get(rec.state, rec.state))

            # Step 2: Actor authorization — only the request owner can submit
            if not rec.employee_id.user_id or rec.employee_id.user_id != self.env.user:
                raise AccessError(_(
                    'Only the request owner can submit this training request.'
                ))

            # Step 3: Business rule validation
            if rec.start_date and rec.end_date and rec.end_date <= rec.start_date:
                raise ValidationError(_(
                    'The end date must be after the start date.'
                ))
            if rec.cost is not None and rec.cost < 0:
                raise ValidationError(_(
                    'Training cost cannot be a negative value.'
                ))

            # Step 4: Execute transition
            rec.state = 'submitted'
        return True

    def action_cancel(self):
        """
        Transition: draft/submitted → cancelled
        Actor:      Request owner
        Guards:     state in ('draft', 'submitted'), owner check
        """
        for rec in self:
            # Step 1: State pre-condition
            if rec.state not in ('draft', 'submitted'):
                raise UserError(_(
                    'Only draft or submitted requests can be cancelled. '
                    'Current status: %s'
                ) % dict(rec._fields['state'].selection).get(rec.state, rec.state))

            # Step 2: Actor authorization — only the request owner can cancel
            if not rec.employee_id.user_id or rec.employee_id.user_id != self.env.user:
                raise AccessError(_(
                    'Only the request owner can cancel this training request.'
                ))

            # Step 4: Execute transition (no additional business rules for cancel)
            rec.state = 'cancelled'
        return True

    def action_manager_approve(self):
        """
        Transition: submitted → manager_approved
        Actor:      The employee's line manager OR any user in group_training_manager
        Guards:     state == 'submitted', manager/group check
        """
        for rec in self:
            # Step 1: State pre-condition
            if rec.state != 'submitted':
                raise UserError(_(
                    'Only submitted requests can be approved at the manager stage. '
                    'Current status: %s'
                ) % dict(rec._fields['state'].selection).get(rec.state, rec.state))

            # Step 2: Actor authorization
            if not (self._is_manager_approver() or self._is_record_manager(rec)):
                raise AccessError(_(
                    'Only the employee\'s line manager or a Training Manager Approver '
                    'can approve at this stage.'
                ))

            # Step 4: Execute transition
            rec.state = 'manager_approved'
        return True

    def action_manager_reject(self):
        """
        Transition: submitted → rejected
        Actor:      The employee's line manager OR any user in group_training_manager
        Guards:     state == 'submitted', manager/group check
        """
        for rec in self:
            # Step 1: State pre-condition
            if rec.state != 'submitted':
                raise UserError(_(
                    'Only submitted requests can be rejected at the manager stage. '
                    'Current status: %s'
                ) % dict(rec._fields['state'].selection).get(rec.state, rec.state))

            # Step 2: Actor authorization
            if not (self._is_manager_approver() or self._is_record_manager(rec)):
                raise AccessError(_(
                    'Only the employee\'s line manager or a Training Manager Approver '
                    'can reject at this stage.'
                ))

            # Step 4: Execute transition
            rec.state = 'rejected'
        return True

    def action_hr_approve(self):
        """
        Transition: manager_approved → hr_approved
        Actor:      Any user in group_training_hr
        Guards:     state == 'manager_approved', HR group check
        """
        for rec in self:
            # Step 1: State pre-condition
            if rec.state != 'manager_approved':
                raise UserError(_(
                    'Only manager-approved requests can receive final HR approval. '
                    'Current status: %s'
                ) % dict(rec._fields['state'].selection).get(rec.state, rec.state))

            # Step 2: Actor authorization — only HR Approvers at this stage
            if not self._is_hr_approver():
                raise AccessError(_(
                    'Only a Training HR Approver can give final approval.'
                ))

            # Step 4: Execute transition
            rec.state = 'hr_approved'
        return True

    def action_hr_reject(self):
        """
        Transition: manager_approved → rejected
        Actor:      Any user in group_training_hr
        Guards:     state == 'manager_approved', HR group check
        """
        for rec in self:
            # Step 1: State pre-condition
            if rec.state != 'manager_approved':
                raise UserError(_(
                    'Only manager-approved requests can be rejected at the HR stage. '
                    'Current status: %s'
                ) % dict(rec._fields['state'].selection).get(rec.state, rec.state))

            # Step 2: Actor authorization
            if not self._is_hr_approver():
                raise AccessError(_(
                    'Only a Training HR Approver can reject at this stage.'
                ))

            # Step 4: Execute transition
            rec.state = 'rejected'
        return True

    def action_reset_to_draft(self):
        """
        Utility: rejected/cancelled → draft (for re-submission).
        Actor:   Request owner.
        Note:    This is a convenience escape hatch for rejected requests;
                 not part of the main FSM but useful in practice.
        """
        for rec in self:
            if rec.state not in ('rejected', 'cancelled'):
                raise UserError(_(
                    'Only rejected or cancelled requests can be reset to draft.'
                ))
            if not rec.employee_id.user_id or rec.employee_id.user_id != self.env.user:
                raise AccessError(_(
                    'Only the request owner can reset this request to draft.'
                ))
            rec.state = 'draft'
        return True
