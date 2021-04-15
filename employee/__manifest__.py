{
    'name': 'Custom employee',
    'summary': """Add more to employee""",
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
        'views/hr_employee_public_views.xml',
    ],
    'installable': True,
    'application': True,
}