import appdaemon.plugins.hass.hassapi as hass
import voluptuous as vol


MODULE = 'toggle_light'
CLASS = 'ToggleLight'

CONF_MODULE = 'module'
CONF_CLASS = 'class'
CONF_ENTITY = 'entity'
CONF_ENTITIES = 'entities'
CONF_OFFSET = 'offset'
CONF_SERVICE_DATA = 'service_data'
CONF_LOG_LEVEL = 'log_level'

LOG_ERROR = 'ERROR'
LOG_DEBUG = 'DEBUG'
LOG_INFO = 'INFO'

STATE_ON = 'on'
STATE_OFF = 'off'

ENTITIES_SCHEMA = vol.Any(
    str,
    { 
        vol.Required(CONF_ENTITY): str,
        vol.Optional(CONF_SERVICE_DATA): dict,
    })

APP_SCHEMA = vol.Schema({
    vol.Required(CONF_MODULE): str,
    vol.Required(CONF_CLASS): str,
    vol.Optional(CONF_ENTITIES): [ ENTITIES_SCHEMA ],
    #vol.Optional(CONF_OFFSET): vol.All(vol.Coerce(int), vol.Range(min=1)),
    vol.Optional(CONF_LOG_LEVEL, default=LOG_DEBUG): vol.Any(LOG_INFO, LOG_DEBUG),
})

class SunsetLights(hass.Hass):
    def initialize(self):
        args = APP_SCHEMA(self.args)

        # Set Lazy Logging (to not have to restart appdaemon)
        self._level = args.get(CONF_LOG_LEVEL)
        self.log(args, level=self._level)

        self._entities = [ AppEntity(e) for e in args.get(CONF_ENTITIES) ]

        self.run_at_sunset(self.entities_on)
        self.run_at_sunrise(self.entities_off)

    def entities_on(self, kwargs):
        self.log("entities_on", level=self._level)
        for ae in self._entities:
            entity_id, attributes = ae.entity_id, ae.attributes
            log_attributes = f' - {attributes}' if attributes else ''
            self.log(f"{STATE_ON} - {entity_id}{log_attributes}", level = self._level)
            if attributes:
                self.turn_on(entity_id, **attributes)
            else:
                self.turn_on(entity_id)

    def entities_off(self, kwargs):
        self.log("entities_off", level=self._level)
        for ae in self._entities:
            self.log(f"{STATE_OFF} - {ae.entity_id}", level = self._level)
            if self.get_state(ae.entity_id) not in [STATE_OFF]:
                self.turn_off(ae.entity_id)

class AppEntity(object):
    def __init__(self, conf):
        self.attributes = {}
        if isinstance(conf, dict):
            self.entity_id = conf.get(CONF_ENTITY)
            self.attributes = conf.get(CONF_SERVICE_DATA, {})
        elif isinstance(conf, str):
            self.entity_id = conf
