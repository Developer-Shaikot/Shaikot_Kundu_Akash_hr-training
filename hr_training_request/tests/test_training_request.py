# -*- coding: utf-8 -*-
from odoo.tests import common
from odoo.exceptions import AccessError, UserError, ValidationError


class TestTrainingRequest(common.TransactionCase):

    @classmethod
    def setUpClass(cls):
        super(TestTrainingRequest, cls).setUpClass()

        # Set up users
        cls.user_employee = cls.env['res.users'].create({
            'name': 'Test Employee',
            'login': 'test_employee',
            'groups_id': [(4, cls.env.ref('hr_training_request.group_training_requester').id), (4, cls.env.ref('base.group_user').id)]
        })
        cls.user_manager = cls.env['res.users'].create({
            'name': 'Test Manager',
            'login': 'test_manager',
            'groups_id': [(4, cls.env.ref('hr_training_request.group_training_manager').id), (4, cls.env.ref('base.group_user').id)]
        })
        cls.user_hr = cls.env['res.users'].create({
            'name': 'Test HR',
            'login': 'test_hr',
            'groups_id': [(4, cls.env.ref('hr_training_request.group_training_hr').id), (4, cls.env.ref('base.group_user').id)]
        })

        # Set up employees
        cls.emp_manager = cls.env['hr.employee'].create({
            'name': 'Manager Employee',
            'user_id': cls.user_manager.id,
        })
        cls.emp_requester = cls.env['hr.employee'].create({
            'name': 'Requester Employee',
            'user_id': cls.user_employee.id,
            'parent_id': cls.emp_manager.id,
        })
        cls.emp_hr = cls.env['hr.employee'].create({
            'name': 'HR Employee',
            'user_id': cls.user_hr.id,
        })

    def test_01_training_request_flow(self):
        """Test the full happy path of the training request."""
        # Employee creates request
        request = self.env['hr.training.request'].with_user(self.user_employee).create({
            'employee_id': self.emp_requester.id,
            'course_name': 'Odoo Development',
            'cost': 1500.0,
            'start_date': '2027-01-01',
            'end_date': '2027-01-05',
        })
        self.assertEqual(request.state, 'draft')

        # Employee submits request
        request.with_user(self.user_employee).action_submit()
        self.assertEqual(request.state, 'submitted')

        # Manager approves
        request.with_user(self.user_manager).action_manager_approve()
        self.assertEqual(request.state, 'manager_approved')

        # HR approves
        request.with_user(self.user_hr).action_hr_approve()
        self.assertEqual(request.state, 'hr_approved')

    def test_02_unauthorized_submit(self):
        """Test that a non-owner cannot submit the request."""
        request = self.env['hr.training.request'].with_user(self.user_employee).create({
            'employee_id': self.emp_requester.id,
            'course_name': 'Odoo Admin',
            'cost': 500.0,
            'start_date': '2027-01-01',
            'end_date': '2027-01-05',
        })
        
        # Manager tries to submit on behalf of employee -> AccessError
        with self.assertRaises(AccessError):
            request.with_user(self.user_manager).action_submit()

    def test_03_invalid_dates(self):
        """Test that end_date cannot be before start_date."""
        with self.assertRaises(ValidationError):
            self.env['hr.training.request'].with_user(self.user_employee).create({
                'employee_id': self.emp_requester.id,
                'course_name': 'Time Travel',
                'cost': 1000.0,
                'start_date': '2027-01-05',
                'end_date': '2027-01-01',
            })
            
    def test_04_negative_cost(self):
        """Test that cost cannot be negative."""
        with self.assertRaises(ValidationError):
            self.env['hr.training.request'].with_user(self.user_employee).create({
                'employee_id': self.emp_requester.id,
                'course_name': 'Free Money',
                'cost': -100.0,
            })

    def test_05_manager_reject_and_reset(self):
        """Test rejection and reset to draft flow."""
        request = self.env['hr.training.request'].with_user(self.user_employee).create({
            'employee_id': self.emp_requester.id,
            'course_name': 'Odoo Testing',
            'cost': 100.0,
        })
        request.with_user(self.user_employee).action_submit()
        
        # Manager rejects
        request.with_user(self.user_manager).action_manager_reject()
        self.assertEqual(request.state, 'rejected')
        
        # Employee resets to draft
        request.with_user(self.user_employee).action_reset_to_draft()
        self.assertEqual(request.state, 'draft')

    def test_06_delete_restriction(self):
        """Test that only draft/cancelled records can be deleted."""
        request = self.env['hr.training.request'].with_user(self.user_employee).create({
            'employee_id': self.emp_requester.id,
            'course_name': 'Odoo Security',
            'cost': 0.0,
        })
        
        # Draft can be deleted
        request.unlink()
        
        # Submitted cannot be deleted
        request2 = self.env['hr.training.request'].with_user(self.user_employee).create({
            'employee_id': self.emp_requester.id,
            'course_name': 'Odoo Security 2',
        })
        request2.with_user(self.user_employee).action_submit()
        
        with self.assertRaises(UserError):
            request2.unlink()
