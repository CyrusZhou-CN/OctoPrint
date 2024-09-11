__license__ = "GNU Affero General Public License http://www.gnu.org/licenses/agpl.html"
__copyright__ = "Copyright (C) 2024 The OctoPrint Project - Released under terms of the AGPLv3 License"

import flask
from flask_babel import gettext

import octoprint.access.permissions
import octoprint.plugin
import octoprint.settings
from octoprint.access.groups import ADMIN_GROUP

from .checks import OK_RESULT


class HealthCheckPlugin(
    octoprint.plugin.AssetPlugin,
    octoprint.plugin.StartupPlugin,
    octoprint.plugin.SimpleApiPlugin,
    octoprint.plugin.TemplatePlugin,
    octoprint.plugin.SettingsPlugin,
):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._checks = {}

    def initialize(self):
        self._initialize_checks()

    def _initialize_checks(self):
        from .checks.filesystem_storage import FilesystemStorageCheck
        from .checks.octoprint_freshness import OctoPrintFreshnessCheck
        from .checks.python_eol import PythonEolHealthCheck

        for clz in (
            OctoPrintFreshnessCheck,
            PythonEolHealthCheck,
            FilesystemStorageCheck,
        ):
            if clz.key in self.disabled_checks:
                continue
            self._checks[clz.key] = clz(self._settings_for_check(clz.key))

        hooks = self._plugin_manager.get_hooks(
            "octoprint.plugin.health_check.get_additional_checks"
        )
        for name, hook in hooks.items():
            try:
                checks = hook()
                for clz in checks:
                    if clz.key in self.disabled_checks:
                        continue
                    self._checks[clz.key] = clz(self._settings_for_check(clz.key))
            except Exception:
                self._logger.exception(
                    f"Error while fetching additional health checks from {name}",
                    extra={"plugin": name},
                )

    @property
    def disabled_checks(self):
        return self._settings.get(["disabled"])

    def check(self, key, force=False):
        self._checks[key].perform_check(force=force)

    def check_all(self, force=False):
        result = {}
        for check in self._checks.values():
            if check.key in self.disabled_checks:
                continue

            try:
                result[check.key] = check.perform_check(force=force)
                if result[check.key] is None:
                    result[check.key] = OK_RESULT
            except Exception:
                self._logger.exception(
                    f"Exception while running health check {check.key}"
                )
        return result

    def _settings_for_check(self, key):
        return self._settings.get(["checks", key], asdict=True, merged=True)

    ##~~ Additional permissions hook

    def get_additional_permissions(self):
        return [
            {
                "key": "CHECK",
                "name": "Perform healthchecks",
                "description": gettext(
                    "Allows to perform health checks and view their results"
                ),
                "roles": ["check"],
                "default_groups": [ADMIN_GROUP],
            },
        ]

    ##~~ Custom events hook

    def register_custom_events(self, *args, **kwargs):
        return ["update_healthcheck"]

    ##~~ SettingsPlugin

    def get_settings_defaults(self):
        return {
            "checks": {
                "python_eol": {
                    "url": "https://get.octoprint.org/python-eol",
                    "ttl": 24 * 60 * 60,
                    "fallback": {
                        "3.7": {"date": "2023-06-27", "last_octoprint": "1.11.*"},
                        "3.8": {"date": "2024-10-31"},
                    },
                },
                "filesystem_storage": {"issue_threshold": 95, "warning_threshold": 85},
            },
            "disabled": [],
        }

    def on_settings_save(self, data):
        result = super().on_settings_save(data)

        for check in self._checks.values():
            check.update_settings(self._settings_for_check(check.key))

        return result

    ##~~ SimpleApiPlugin

    def on_api_get(self, request):
        if not octoprint.access.permissions.Permissions.PLUGIN_HEALTH_CHECK_CHECK.can():
            flask.abort(403)

        result = self.check_all(
            force=request.values.get("refresh") in octoprint.settings.valid_boolean_trues
        )

        return flask.jsonify(health={k: v.model_dump() for k, v in result.items()})

    ##~~ TemplatePlugin

    def get_template_configs(self):
        return [
            {
                "type": "navbar",
                "template": "health_check_navbar.jinja2",
                "styles": ["display: none"],
                "data_bind": "visible: loginState.hasPermission(access.permissions.PLUGIN_HEALTH_CHECK_CHECK)",
            },
        ]


__plugin_name__ = "Healthcheck Plugin"
__plugin_author__ = "Gina Häußge"
__plugin_description__ = "Checks your OctoPrint"
__plugin_disabling_discouraged__ = gettext(
    "Without this plugin you might miss problematic issues with your "
    "OctoPrint installation."
)
__plugin_license__ = "AGPLv3"
__plugin_pythoncompat__ = ">=3.7,<4"
__plugin_implementation__ = HealthCheckPlugin()

__plugin_hooks__ = {
    "octoprint.access.permissions": __plugin_implementation__.get_additional_permissions,
    "octoprint.events.register_custom_events": __plugin_implementation__.register_custom_events,
}
