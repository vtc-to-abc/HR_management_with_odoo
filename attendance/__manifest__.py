{
    'name': 'Custom attendance',
    'summary': """Add more to attendance""",
    'description': """yeah""",
    'author': "still me",
    'website': "https://cons.us",
    'category': 'Uncategorized',
    'version': '0.1',
    'depends': [
        'hr', 'barcodes', 'hr_attendance'
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/hr_attendance_custom_views.xml',
    ],
    'installable': True,
    'application': True,
}