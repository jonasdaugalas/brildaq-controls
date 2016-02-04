/* jshint esnext: true */
angular.module("web-config").controller("OverviewCtrl", ["$http", "Configurations", function($http, Cfgs) {

    var me = this;
    this.configurations = [];
    this.configTree = {};
    this.owners = [];
    this.owner = "";
    this.running = [];
    this.getRunningSuccess = true;

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

    this.refreshStatuses = function(soft) {
        var url = soft ? "/running_soft" : "/running";
        $http.get(url).then(function(response) {
            me.running = response.data;
            me.getRunningSuccess = true;
            return true;
        }, function(response) {
            me.running = [];
            me.getRunningSuccess = false;
            return false;
        }).then(function(success) {
            console.log(success);
            console.log(me.running);
            console.log(me.getRunningSuccess);
            var running, paths = [];
            for (running of me.running) {
                paths.push(running);
            }
            var putRunningFlag = function(leaf) {
                leaf._running = (
                    success ? paths.indexOf(leaf._path) > -1 : null);
            };
            itterateConfigTree(me.configTree, putRunningFlag);
        });
    };

    this.getConfigXML = function(path) {
        $http.get("/configxml" + path).then(function(response) {
            return response.data;
        }, function(response) {
            //TODO: ALERT
            console.error("Failed getting configuration xml", path);
        });
    };

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

    this.init();
}]);
