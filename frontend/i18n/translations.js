translations = {
    'en': {
        'welcome': 'Welcome to FasalMitra',
        'dashboard': 'Dashboard',
    },
    'hi': {
        'welcome': 'FasalMitra me svagat hai',
        'dashboard': 'Dashboard',
    }
}

def get_translation(lang, key):
    return translations.get(lang, {}).get(key, translations['en'].get(key, key))

