$(function () {
    function ConnectionViewModel(parameters) {
        var self = this;

        self.loginState = parameters[0];
        self.settings = parameters[1];
        self.printerProfiles = parameters[2];
        self.access = parameters[3];

        self.allViewModels = undefined;

        self.serialConnector = {
            portOptions: ko.observableArray([]),
            baudrateOptions: ko.observableArray([]),
            currentPort: ko.observable(),
            currentBaudrate: ko.observable()
        };
        self.serialConnector.validPort = ko.pureComputed(
            () =>
                !self.connectionOptionsFetched() ||
                self.serialConnector.portOptions().length > 0 ||
                self.settings.settings.serial.ignoreEmptyPorts()
        );
        self.serialConnector.portCaption = ko.pureComputed(() =>
            self.serialConnector.validPort() ? "AUTO" : gettext("No serial port found")
        );
        self.serialConnector.enablePort = ko.pureComputed(
            () => self.serialConnector.validPort() && self.isErrorOrClosed()
        );

        self.printerProfiles.profiles.items.subscribe(function () {
            var allProfiles = self.printerProfiles.profiles.items();

            var printerOptions = [];
            _.each(allProfiles, function (profile) {
                printerOptions.push({id: profile.id, name: profile.name});
            });
            self.profileOptions(printerOptions);
        });

        self.printerProfiles.currentProfile.subscribe(function () {
            self.currentProfile(self.printerProfiles.currentProfile());
        });

        self.connectionOptionsFetched = ko.observable(false);
        self.selectedConnector = ko.observable(undefined);
        self.connectorOptions = ko.observableArray([]);
        self.connectorParameters = {};

        self.currentConnector = ko.observable(undefined);
        self.currentConnectorParameters = {};

        self.profileOptions = ko.observableArray(undefined);
        self.currentProfile = ko.observable(undefined);

        self.saveSettings = ko.observable(undefined);
        self.autoconnect = ko.observable(undefined);

        self.isErrorOrClosed = ko.observable(undefined);
        self.isOperational = ko.observable(undefined);
        self.isPrinting = ko.observable(undefined);
        self.isPaused = ko.observable(undefined);
        self.isError = ko.observable(undefined);
        self.isReady = ko.observable(undefined);
        self.isLoading = ko.observable(undefined);

        self.enableConnect = ko.pureComputed(function () {
            //return self.enablePort() || !self.isErrorOrClosed();
            return true; // enable always for now, until we have an auto refresh in 1.9.0
        });

        self.buttonText = ko.pureComputed(function () {
            if (self.isErrorOrClosed()) return gettext("Connect");
            else return gettext("Disconnect");
        });

        self.enableSaveSettings = ko.pureComputed(function () {
            return self.enableConnect() && self.isErrorOrClosed();
        });

        self.enableAutoConnect = ko.pureComputed(function () {
            return self.enableConnect() && self.isErrorOrClosed();
        });

        self.previousIsOperational = undefined;

        self.refreshVisible = ko.observable(true);

        self.requestData = function () {
            if (!self.loginState.hasPermission(self.access.permissions.CONNECTION)) {
                return;
            }

            OctoPrint.connection.getSettings().done(self.fromResponse);
        };

        self.fromResponse = function (response) {
            const connectors = response.options.connectors;
            const currentConnector = response.current.connector;
            const preferredConnector = response.options.preferredConnector.connector;

            self.connectorOptions(connectors);

            const connectorParameters = {};
            connectors.forEach((item) => {
                connectorParameters[item.connector] = item.parameters;
            });
            self.connectorParameters = connectorParameters;

            if (currentConnector && connectorParameters[currentConnector]) {
                self.selectedConnector(currentConnector);
            } else {
                self.selectedConnector(connectors[0].connector);
            }

            // serial connector

            const ports = connectorParameters.serial.port;
            const baudrates = connectorParameters.serial.baudrate;

            const currentPort =
                currentConnector === "serial" ? response.current.parameters.port : null;
            const currentBaudrate =
                currentConnector === "serial" ? response.current.baudrate : null;

            const preferredPort =
                preferredConnector == "serial"
                    ? response.options.preferredConnector.parameters.port
                    : null;
            const preferredBaudrate =
                preferredConnector == "serial"
                    ? response.options.preferredConnector.parameters.baudrate
                    : null;

            self.serialConnector.portOptions(ports);
            self.serialConnector.baudrateOptions(baudrates);

            if (!self.serialConnector.currentPort() && ports) {
                if (currentPort && ports.indexOf(currentPort) >= 0) {
                    self.serialConnector.currentPort(currentPort);
                } else if (preferredPort && ports.indexOf(preferredPort) >= 0) {
                    self.serialConnector.currentPort(preferredPort);
                }
            }

            if (!self.serialConnector.currentBaudrate() && baudrates) {
                if (currentBaudrate && baudrates.indexOf(currentBaudrate) >= 0) {
                    self.serialConnector.currentBaudrate(currentBaudrate);
                } else if (
                    preferredBaudrate &&
                    baudrates.indexOf(preferredBaudrate) >= 0
                ) {
                    self.serialConnector.currentBaudrate(preferredBaudrate);
                }
            }

            // other connectors

            callViewModels(self.allViewModels, "onConnectionDataReceived", [
                response.current,
                connectorParameters,
                response.preferredConnector
            ]);

            // printer profile

            const printerProfiles = response.options.printerProfiles;
            const preferredProfile = response.options.preferredProfile;
            const currentProfile = response.current.printerProfile;

            if (!self.currentProfile() && printerProfiles) {
                if (printerProfiles.indexOf(currentProfile) >= 0) {
                    self.currentProfile(currentProfile);
                } else if (printerProfiles.indexOf(preferredProfile) >= 0) {
                    self.currentProfile(preferredProfile);
                }
            }

            self.saveSettings(false);
            self.connectionOptionsFetched(true);
        };

        self.fromHistoryData = function (data) {
            self._processStateData(data.state);
        };

        self.fromCurrentData = function (data) {
            self._processStateData(data.state);
        };

        self.openOrCloseOnStateChange = function (force) {
            if (!self._startupComplete && !force) return;

            var connectionTab = $("#connection");
            if (self.isOperational() && connectionTab.hasClass("in")) {
                connectionTab.collapse("hide");
                self.refreshVisible(false);
            } else if (!self.isOperational() && !connectionTab.hasClass("in")) {
                connectionTab.collapse("show");
                self.refreshVisible(true);
            }
        };

        self._processStateData = function (data) {
            self.previousIsOperational = self.isOperational();

            self.isErrorOrClosed(data.flags.closedOrError);
            self.isOperational(data.flags.operational);
            self.isPaused(data.flags.paused);
            self.isPrinting(data.flags.printing);
            self.isError(data.flags.error);
            self.isReady(data.flags.ready);
            self.isLoading(data.flags.loading);

            if (self.previousIsOperational !== self.isOperational()) {
                // only open or close if the panel is visible (for admins) and
                // the state just changed to avoid thwarting manual open/close
                self.openOrCloseOnStateChange();
            }
        };

        self.connect = function () {
            if (self.isErrorOrClosed()) {
                const connector = self.selectedConnector();
                const profile = self.currentProfile();

                const parameters = {};
                const container = $(`#connection_options_${connector}`);
                _.each(["input", "select", "textarea"], (tag) => {
                    $(`${tag}[data-connection-parameter]`, container).each(
                        (index, element) => {
                            const jqueryElement = $(element);
                            const parameter = jqueryElement.data("connection-parameter");
                            parameters[parameter] = jqueryElement.val();
                        }
                    );
                });

                const data = {
                    connector: connector,
                    parameters: parameters,
                    printerProfile: profile,
                    autoconnect: self.settings.serial_autoconnect()
                };

                if (self.saveSettings()) data["save"] = true;

                OctoPrint.connection.connect(data).done(function () {
                    self.settings.requestData();
                    self.settings.printerProfiles.requestData();
                });
            } else {
                if (!self.isPrinting() && !self.isPaused()) {
                    self.requestData();
                    OctoPrint.connection.disconnect();
                } else {
                    showConfirmationDialog({
                        title: gettext("Are you sure?"),
                        message: gettext(
                            "<p><strong>You are about to disconnect from the printer while a print " +
                                "is in progress.</strong></p>" +
                                "<p>Disconnecting while a print is in progress will prevent OctoPrint from " +
                                "completing the print. If you're printing from an SD card attached directly " +
                                "to the printer, any attempt to restart OctoPrint or reconnect to the printer " +
                                "could interrupt the print.<p>"
                        ),
                        question: gettext(
                            "Are you sure you want to disconnect from the printer?"
                        ),
                        cancel: gettext("Stay Connected"),
                        proceed: gettext("Disconnect"),
                        onproceed: function () {
                            self.requestData();
                            OctoPrint.connection.disconnect();
                        }
                    });
                }
            }
        };

        self.onEventSettingsUpdated = function () {
            self.requestData();
        };

        self.onEventConnected = function () {
            self.requestData();
        };

        self.onEventDisconnected = function () {
            self.requestData();
        };

        self.onEventConnectionsAutorefreshed = function () {
            self.requestData();
        };

        self.onAllBound = function (allViewModels) {
            self.allViewModels = allViewModels;
        };

        self.onStartup = function () {
            var connectionTab = $("#connection");
            connectionTab.on("show", function () {
                self.refreshVisible(true);
            });
            connectionTab.on("hide", function () {
                self.refreshVisible(false);
            });
        };

        self.onStartupComplete = function () {
            self.openOrCloseOnStateChange(true);
        };

        self.onUserPermissionsChanged =
            self.onUserLoggedIn =
            self.onUserLoggedOut =
                function () {
                    self.requestData();
                };
    }

    OCTOPRINT_VIEWMODELS.push({
        construct: ConnectionViewModel,
        dependencies: [
            "loginStateViewModel",
            "settingsViewModel",
            "printerProfilesViewModel",
            "accessViewModel"
        ],
        elements: ["#connection_wrapper"]
    });
});
