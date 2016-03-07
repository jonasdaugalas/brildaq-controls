/* jshint esnext: true */
angular.module("web-config").controller("OverviewCtrl", ["$rootScope", "$http", "$timeout", "CLIENT_CONSTS", "Timers", "Configurations", function($rootScope, $http, $timeout, CONSTS, Timers, Cfgs) {

    var me = this;
    // all configurations' paths
    this.paths = [];
    // map path to newest configuration version
    this.versions = {};
    this.tree = {};
    this.owners = [];
    // running configurations' paths
    this.running = [];
    // map path to {URI: ..., version: ..., resGID: ... }
    this.runningConfigsDetails = {};
    // Running query was successful
    this.isSuccessGetRunning = false;
    // map path to state
    this.states = {};
    this.isSuccessGetStates = false;
    // array of active (running and state is "ON" or "Error) cfg paths
    this.active = [];
    this.configData = {};
    // flag if there is configuration in state 'GoingOn', 'GoingOff', 'Resetting'
    me.hasChangingStates = false;

    var srvendp = CONSTS.server_endpoint;
    var refreshTimer = null;

    this.init = function() {
        me.refreshConfigurations().then(function() {
            refreshTimer = Timers.create(50000);
            refreshTimer.addAction({callable: refresher});
        });
    };

    this.refreshConfigurations = function() {
        // ask confgigurations service to update info about existing
        // configurations
        return Cfgs.update().then(function(paths) {
            // construct configuration tree
            var path, pArr, node, head, flags, cfg;
            me.paths = paths;
            me.versions = {};
            me.tree = {};
            for (path of paths) {
                me.versions[path] = Cfgs.getVersion(path);
                pArr = path.split("/");
                pArr.shift();
                head = me.tree;
                for (node of pArr) {
                    if (!head.hasOwnProperty(node)) {
                        head[node] = {};
                    }
                    head = head[node];
                }
                head._isLeaf = true;
                head._path = path;
                cfg = Cfgs.get(path);
                console.log(cfg);
                flags = cfg.flags;
                console.log(flags);
                if (typeof flags !== "undefined") {
                    head._flags = flags;
                }
            }
            // end of construct configuration tree
            // determine owners
            me.owners = Object.keys(me.tree);
            console.log(me.tree);
            return me.refreshStatuses();
        });
    };

    this.refreshStatuses = function() {
        return getRunning().then(function() {
            return getStates(me.running);
        }).then(function() {
            me.getActiveConfigData();
            var path;
            var putRunningFlag = function(leaf) {
                if (me.isSuccessGetRunning) {
                    leaf._running = me.running.indexOf(leaf._path) > -1;
                    leaf._state = me.states[leaf._path];
                } else {
                    leaf._running = null;
                }
            };
            itterateConfigTree(me.tree, putRunningFlag);
            if (me.hasChangingStates) {
                $timeout(me.refreshStatuses, 4000);
            }
        });
    };

    function getRunning() {
        return $http.get(srvendp + "/running/" + $rootScope.globals.owner)
            .then(function(response) {
                var path;
                me.runningDetails = response.data;
                me.running = [];
                for (path in response.data) {
                    if (response.data.hasOwnProperty(path)) {
                        me.running.push(path);
                    }
                }
                me.isSuccessGetRunning = true;
                return true;
            }).catch(function(response) {
                me.running = [];
                me.isSuccessGetRunning = false;
                return false;
            });
    }

    function getStates(paths) {
        var running, uris =[];
        me.states = {};
        me.active = [];
        if (paths.length < 1) {
            return Promise.resolve();
        }
        for (running of paths) {
            uris.push(Cfgs.path2URI(running));
        }
        return $http.post(srvendp + "/states", uris).then(function(response) {
            var uri, path;
            me.hasChangingStates = false;
            for (uri in response.data) {
                if (response.data.hasOwnProperty(uri)) {
                    path = Cfgs.URI2path(uri);
                    me.states[path] = response.data[uri];
                    if (response.data[uri] === "ON" ||
                        response.data[uri] === "Error") {
                        me.active.push(path);
                    }
                    if (response.data[uri] === "GoingOn" ||
                        response.data[uri] === "GoingOff" ||
                        response.data[uri] === "Resetting") {
                        me.hasChangingStates = true;;
                    }
                }
            }
            me.isSuccessGetStates = true;
        }).catch(function(response) {
            me.isSuccessGetStates = false;
            console.log("Failed getting states", response);
        });
    }


    this.getActiveConfigData = function() {
        var path;
        function getConfigClosure (p) {
            $http.get(srvendp + "/config" + p + "/v=" + me.runningDetails[p].version)
                .then(function(response) {
                    me.configData[p] = response.data;
                }).catch(function(response) {
                    console.log(response);
                    me.configData[p] = null;
                });
        }
        for (path of me.active) {
            getConfigClosure(path);
        }
    };

    // this.getConfigXML = function(path) {
    //     $http.get("/configxml" + path).then(function(response) {
    //         return response.data;
    //     }, function(response) {
    //         //TODO: ALERT
    //         console.error("Failed getting configuration xml", path);
    //     });
    // };

    function itterateConfigTree(node, visit) {
        var stack = [node];
        var key;
        while(stack.length !== 0) {
            node = stack.pop();
            if (node._isLeaf) {
                visit(node);
            } else {
                for (key in node) {
                    if (node.hasOwnProperty(key)) {
                        stack.push(node[key]);
                    }
                }
            }
        }
    }

    this.sendCommand = function(cmd, path) {
        return $http.post(srvendp + "/send/" + cmd,
                          JSON.stringify(Cfgs.path2URI(path)))
            .then(dummyHttpHandler)
            .catch(dummyHttpHandler);
    };

    this.create = function(path) {
        return $http.post(srvendp + "/create", JSON.stringify(Cfgs.path2URI(path)))
            .then(dummyHttpHandler)
            .catch(dummyHttpHandler);
    };


    this.destroy = function(path) {
        return $http.post(srvendp + "/destroy", JSON.stringify(Cfgs.path2URI(path)))
            .then(dummyHttpHandler)
            .catch(dummyHttpHandler);
    };


    this.getDangerFlags = function(path) {
        var flags = Cfgs.get(path).flags;
        if (!flags) {
            return undefined;
        }
        return flags.DANGER;
    };

    function dummyHttpHandler(response) {
        console.log(response);
        me.refreshStatuses();
    }

    var refresher = (function() {
        var counter = 0;
        return function() {
            counter += 1;
            if (counter > 240) {
                counter = 0;
                console.log("Full refresh");
                me.refreshConfigurations();
            } else {
                console.log("Refreshing states");
                me.refreshStatuses();
            }
        };
    })();

    this.init();
}]);
