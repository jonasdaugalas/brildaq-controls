/* jshint esnext: true */
angular.module("web-config").controller("OverviewCtrl", ["$http", "Configurations", function($http, Cfgs) {

    var me = this;
    // all configurations' paths
    this.configurations = [];
    this.configTree = {};
    this.owners = [];
    // selected owner
    this.owner = "";
    // running configurations' paths
    this.running = [];
    // Running query was successful
    this.getRunningSuccess = true;
    // map path to state
    this.states = {};
    // array of active (running and state is not "OFF") cfg paths
    this.active = [];
    this.activeConfigs = {};

    this.init = function() {
        me.refreshConfigurations().then(function() {
            me.owner = me.owners[0];
        });
    };

    this.refreshConfigurations = function() {
        return Cfgs.update().then(function(paths) {
            var path, parr, node, head;
            me.configurations = paths;
            for (path of paths) {
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
            me.refreshStatuses();
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
        });
    };

    function getRunning() {
        return $http.get("/running").then(function(response) {
            me.running = response.data;
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
        return $http.post('/states', uris).then(function(response) {
            var uri, path;
            for (uri in response.data) {
                if (response.data.hasOwnProperty(uri)) {
                    path = Cfgs.URI2path(uri);
                    me.states[path] = response.data[uri];
                    if (response.data[uri] === "ON" ||
                        response.data[uri] === "Error") {
                        me.active.push(path);
                    }
                }
            }
        }).catch(function(response) {
            console.log("Failed getting states", response);
        });
    }


    this.getActiveConfigs = function() {
        var path;
        for (path of me.active) {
            (function (p) {
                $http.get("/config" + p).then(function(response) {
                    me.activeConfigs[p] = response.data;
                }).catch(function(response) {
                    console.log(response);
                    me.activeConfigs[p] = null;
                });
            })(path);
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
        return $http.post("/send/" + cmd,
                          JSON.stringify(Cfgs.path2URI(path)))
            .then(function(response) {
                console.log(response);
                me.refreshStatuses();
            })
            .catch(function(response) {
                console.log(response);
                me.refreshStatuses();
            });
    };

    this.init();
}]);
