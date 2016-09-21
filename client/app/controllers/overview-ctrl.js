/* jshint esnext: true */
angular.module("web-config").controller("OverviewCtrl", ["$rootScope", "$http", "$timeout", "CONST", "Timers", "Modals", "Alerts", "Alarm", "Configurations", function($rootScope, $http, $timeout, CONST, Timers, Modals, Alerts, Alarm, Configs) {
    var me = this;
    var srvendp = CONST.server_endpoint;
    var scheduledUpdate = false;
    var scheduledUpdateTimeout = 4000;
    var whitelist = null;
    var blacklist = null;
    var configs = {};
    var states = {};

    console.log(Alarm);

    this.alarmIsMute = Alarm.isMute();
    this.alarmIsPlaying = Alarm.isPlaying();
    this.refreshTimer = null;
    this.paths = null;
    this.tree = null;
    this.owners = null;
    this.pathToVersion = null;
    this.pathToState = null;
    this.activePaths = null;
    this.runningDetails = null;
    this.activeConfigDetails = null;
    this.successGetConfigs = false;
    this.successGetRunning = false;
    this.successGetStates = false;

    this.init = function() {
        whitelist = CONST.profiles[$rootScope.globals.profileName].whitelist || null;
        blacklist = CONST.profiles[$rootScope.globals.profileName].blacklist || null;
        me.updateConfigs();
        me.refreshTimer = Timers.create(56000);
        me.refreshTimer.addAction({callable: refresher});
        console.log(document.cookie);
        if (document.cookie.indexOf('clientname') < 0) {
            Alerts.pushNameAlert();
        }
    };

    this.updateConfigs = function() {
        return Configs.getConfigs(whitelist, blacklist)
            .then(function(newConfigs) {
                var path;
                configs = newConfigs;
                me.paths = configs.paths;
                me.pathToVersion = {};
                for (path of me.paths) {
                    me.pathToVersion[path] = configs.configs[path].version;
                }
                me.tree = buildTree(me.paths);
                me.owners = Object.keys(me.tree.childNodes);
                me.successGetConfigs = true;
                return me.updateStates();
            }, function() {
                me.successGetConfigs = false;
                return Promise.reject();
            });
    };

    this.updateStates = function() {
        scheduledUpdate = false;
        return getRunning().then(getStates).then(function(newStates) {
            if (needAlarm(states, newStates)) {
                me.playAlarm();
            }
            states = newStates;
            me.pathToState = configs.pathKeys(states.states);
            me.activePaths = configs.getPaths(states.active);
            if (states.hasChangingStates && !scheduledUpdate) {
                me.scheduleStatusUpdate();
                return;
            }
            me.getActiveConfigDetails();
        });
    };

    this.scheduleStatusUpdate = function() {
        if (scheduledUpdate) {
            return Promise.reject();
        }
        scheduledUpdate = true;
        return $timeout(me.updateStates, scheduledUpdateTimeout);
    };

    function getRunning() {
        return Configs.getRunning($rootScope.globals.owner)
            .then(function(running) {
                var path, runningPaths = [];
                var paths = Object.keys(running);
                me.runningDetails = running;
                for (path of paths) {
                    if (me.paths.indexOf(path) >= 0) {
                        runningPaths.push(path);
                    }
                }
                me.successGetRunning = true;
                return configs.getUris(runningPaths);
            }, function(response) {
                me.successGetRunning = false;
                return Promise.reject();
            });
    }

    function getStates(paths) {
        return Configs.getStates(paths).then(function(newStates) {
            me.successGetStates = true;
            return newStates;
        }, function() {
            console.log('failed get states');
            me.successGetStates = false;
            return Promise.reject();
        });
    }

    function needAlarm(oldStates, newStates) {
        var uri;
        for (uri of Object.keys(newStates)) {
            if (oldStates[uri] && oldStates[uri] === "ON") {
                if (newStates[uri] === "Error") {
                    return true;
                }
            }
        }
        return false;
    }

    function buildTree(paths) {
        var path, pArr, node, head, flags, cfg, lastId = 0;
        me.tree = {
            _id: ++lastId,
            childNodes: {}
        };
        for (path of paths) {
            pArr = path.split("/");
            pArr.shift();
            head = me.tree;
            for (node of pArr) {
                if (!head.childNodes.hasOwnProperty(node)) {
                    head.childNodes[node] = {
                        _id: ++lastId,
                        childNodes: {}
                    };
                }
                head = head.childNodes[node];
            }
            head._isLeaf = true;
            head._path = path;
        }
        return me.tree;
    }

    this.getActiveConfigDetails = function() {
        var path, promises = [];
        function getConfigClosure (p) {
            return Configs.getConfigDetails(p, me.runningDetails[p].version, false)
                .then(function(details) {
                    me.activeConfigDetails[p] = details;
                });
        }
        me.activeConfigDetails = {};
        for (path of me.activePaths) {
            promises.push(getConfigClosure(path));
        }
        return Promise.all(promises);
    };

    this.sendCommand = function(cmd, path) {
        return Configs.sendCommand(cmd, configs.pathToUri[path])
            .then(afterActionHandler, afterActionHandler);
    };

    this.create = function(path) {
        return Configs.create(configs.pathToUri[path])
            .then(afterActionHandler, afterActionHandler);
    };

    this.destroy = function(path) {
        var modal = Modals.confirmModal(
            "Annoying confirmation",
            "Destroying function managers is only needed when changing "
                + "configurations. 'TurnOFF' and 'Reset' are "
                + "enough for restarting processes.",
            "Destroy", "Cancel");
        return modal.result.then(function() {
            return Configs.destroy(configs.pathToUri[path])
                .then(afterActionHandler, afterActionHandler);
        });
    };

    this.toggleAlarmMute = function() {
        Alarm.toggleMute();
        me.alarmIsMute = Alarm.isMute();
    };

    this.playAlarm = function() {
        Alarm.play();
    };

    function afterActionHandler(data) {
        console.log(data);
        me.updateStates();
    }

    function checkAppVersion() {
        $http.get(srvendp + '/appv').then(function(response) {
            console.log(response.data);
            if (APP_TIME < response.data) {
                Alerts.pushReloadAlert();
            }
        });
    };

    var refresher = (function() {
        var counter = 0;
        return function() {
            counter += 1;
            if (counter > 240) {
                counter = 0;
                console.log("Check for new configurations");
                me.updateConfigs();
                if (document.cookie.indexOf('clientname') < 0) {
                    if (Alerts.alertByTypeExists('name')) {
                        Alerts.pushNameAlert();
                    }
                }
            } else {
                if (counter % 10 == 0) {
                    checkAppVersion();
                }
                me.updateStates();
            }
        };
    })();

    this.init();
}]);
