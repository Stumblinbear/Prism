import json
import os

import prism
import settings

import api

class JSONConfig(object):
    def __init__(self, obj=None, filename=None, path=None, auto_save=True):
        if obj is not None:
            if filename is None:
                filename = 'config.json'

            if isinstance(obj, api.BasePlugin):
                self.path = os.path.join(obj.data_folder, filename)
            else:
                self.path = os.path.join(obj, filename)
        elif path is not None:
            self.path = path
        else:
            prism.output('Error: Attmpted to create a config file with no path.')

        self.auto_save = auto_save

        if not os.path.exists(self.path):
            self.__dict__.update({})
        else:
            self.__dict__.update(json.loads(open(self.path).read()))

    def save(self):
        config = dict([(k, v) for k, v in self.__dict__.items() if not k.startswith('_')])
        if len(config) == 0:
            # If there are no config values, just delete it
            if os.path.exists(self.path):
                os.remove(path)
        else:
            # Write to config
            os.makedirs(os.path.dirname(self.path), exist_ok=True)
            with open(self.path, 'w') as file:
                json.dump(config, file, indent=4, sort_keys=True)

    def __getitem__(self, key):
        return self.__dict__[key]

    def __setitem__(self, key, value):
        self.__dict__[key] = value

        if self.auto_save:
            self.save()

    def __delitem__(self, key):
        del self.__dict__[key]

    def __contains__(self, key):
        return key in self.__dict__

    def __len__(self):
        return len(self.__dict__)

    def __repr__(self):
        return repr(self.__dict__)

    def __call__(self, key, default=None):
        if key in self:
            return self[key]
        self[key] = default
        return default

class LocaleConfig(object):
    def __init__(self, obj):
        locale = settings.PRISM_CONFIG['locale']

        if isinstance(obj, api.BasePlugin):
            self.path = os.path.join(obj.plugin_folder, 'locale', locale)
        else:
            self.path = os.path.join(obj, 'locale', locale)

        if not os.path.exists(self.path) and locale != 'en_US':
            locale = 'en_US'

            if isinstance(obj, api.BasePlugin):
                self.path = os.path.join(obj.plugin_folder, 'locale', 'en_US')
            else:
                self.path = os.path.join(obj, 'locale', 'en_US')

            if isinstance(obj, api.BasePlugin):
                prism.output('Locale Warning: Plugin does not have a locale for %s. Offender: %s falling back to en_US.' % (locale, obj.name))
            else:
                prism.output('Locale Warning: Prism does not have a locale for %s. Falling back to en_US.' % locale)

        if not os.path.exists(self.path):
            prism.output('Locale Error: Failed to load locale. %s does not exist. Offender: %s' % (locale, obj.name if isinstance(obj, api.BasePlugin) else 'Prism'))
            return

        with open(self.path) as f:
            for line in f:
                if '=' in line:
                    name, value = line.split('=', 1)
                    self.__dict__[name] = value.rstrip('\r\n')

    def __getitem__(self, key):
        if key not in self.__dict__:
            return key
        return self.__dict__[key]
