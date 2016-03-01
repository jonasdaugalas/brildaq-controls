/* jshint esnext: true */
angular.module("web-config").controller("OverviewCtrl", ["$http", "$timeout", "CLIENT_CONSTS", "Timers", "Configurations", function($http, $timeout, CONSTS, Timers, Cfgs) {

    var me = this;
    // all configurations' paths
    this.configurations = [];
    // map path to newest configuration version
    this.versions = {};
    this.configTree = {};
    this.owners = [];
    // running configurations' paths
    this.running = [];
    // map path to {URI: ..., version: ..., resGID: ... }
    this.runningDetails = {};
    // Running query was successful
    this.getRunningSuccess = true;
    // map path to state
    this.states = {};
    // array of active (running and state is "ON" or "Error) cfg paths
    this.active = [];
    this.activeConfigs = {};
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
        return Cfgs.update().then(function(paths) {
            var path, parr, node, head;
            me.configurations = paths;
            me.versions = {};
            me.configTree = {};
            for (path of paths) {
                me.versions[path] = Cfgs.getVersion(path);
                parr = path.split("/");
                parr.shift();
                head = me.configTree;
                for (node of parr) {
                    if (!head.hasOwnProperty(node)) {
                        head[node] = {};
                    }
                    head = head[node];
                }
                head._isLeaf = true;
                head._path = path;
            }
            me.owners = Object.keys(me.configTree);
            console.log(me.configTree);
            return me.refreshStatuses();
        });
    };

    this.refreshStatuses = function() {
        return getRunning().then(function() {
            return getStates(me.running);
        }).then(function() {
            me.getActiveConfigs();
            var path;
            var putRunningFlag = function(leaf) {
                if (me.getRunningSuccess) {
                    leaf._running = me.running.indexOf(leaf._path) > -1;
                    leaf._state = me.states[leaf._path];
                } else {
                    leaf._running = null;
                }
            };
            itterateConfigTree(me.configTree, putRunningFlag);
            if (me.hasChangingStates) {
                $timeout(me.refreshStatuses, 4000);
            }
        });
    };

    function getRunning() {
        return $http.get(srvendp + "/running").then(function(response) {
            var path;
            me.runningDetails = response.data;
            me.running = [];
            for (path in response.data) {
                if (response.data.hasOwnProperty(path)) {
                    me.running.push(path);
                }
            }
            me.getRunningSuccess = true;
            return true;
        }, function(response) {
            me.running = [];
            me.getRunningSuccess = false;
            return false;
        });
    }

    function getStates(paths) {
        var running, uris =[];
        for (running of paths) {
            uris.push(Cfgs.path2URI(running));
        }
        me.states = {};
        me.active = [];
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
        }).catch(function(response) {
            console.log("Failed getting states", response);
        });
    }


    this.getActiveConfigs = function() {
        var path;
        function getConfigClosure (p) {
            $http.get(srvendp + "/config" + p + "/v=" + me.runningDetails[p].version)
                .then(function(response) {
                    me.activeConfigs[p] = response.data;
                }).catch(function(response) {
                    console.log(response);
                    me.activeConfigs[p] = null;
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
