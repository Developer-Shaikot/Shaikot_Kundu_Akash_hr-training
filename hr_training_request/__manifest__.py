# -*- coding: utf-8 -*-
{
    'name': 'HR Training Request',
    'version': '17.0.1.0.0',
    'category': 'Human Resources',
    'summary': 'Employee training request and multi-stage approval workflow',
    'description': """
        Allows employees to request external training or certifications.
        Routes requests through manager and HR approval with role-gated
        state transitions, record-level security, and role-aware views.
    """,
    'author': 'HSG',
    'depends': ['hr', 'mail'],
    'data': [
        # Security — order matters: groups first, then ACL, then rules
        'security/groups.xml',
        'security/ir.model.access.csv',
        'security/ir_rules.xml',
        # Views
        'views/hr_training_request_views.xml',
        'views/hr_employee_views.xml',
        'views/menus.xml',
    ],
    'demo': [
        'data/demo_data.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
