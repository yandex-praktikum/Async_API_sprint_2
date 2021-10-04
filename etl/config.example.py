config = {
    'main': {
        # critical - 5, error - 4, warning - 3, info - 2, debug - 1
        'log_level': 1,
        'log_to_file': False,
        'log_filename': 'etl.log',
        'state_filename': 'state.txt',
    },

    'postgresql': {
        'dbname': 'django-movies',
        'host': '127.0.0.1',
        'port': 5432,
        'user': 'postgres',
        'password': 'postgres',
        'options': '-c search_path=movies,public',
        # Задержка между запросами в секундах
        'query_delay': 0.1,
    },

    'elasticsearch': {
        'url': 'http://127.0.0.1:9200',
    }
}
