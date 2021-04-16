{
    'name': 'Custom timeoff',
    'summary': """Add more to timeoff""",
    'description': """yeah""",
    'author': "still me",
    'website': "https://cons.us",
    'category': 'Uncategorized',
    'version': '0.1',
    'depends': [
        'hr', 'hr_contract', 'hr_holidays'
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/hr_leave_allocation_views.xml',
        'views/hr_leave_views.xml',
    ],
    'installable': True,
    'application': True,
}