config = {
        'dev': {
            'SQLALCHEMY_DATABASE_URI': 'sqlite:///test.db',
        },
        'production': {
            'SQLALCHEMY_DATABASE_URI': 'postgresql://logger:logger@postgres/logger',
        },
}
