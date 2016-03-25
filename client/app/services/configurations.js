angular.module("web-config").service("Configurations", ["$http", "CONSTS", function($http, CONSTS) {
    var me = this;

    this.configurations = {};
    this.paths = [];

    var RE_FULPATH = /.*?fullpath=(.*?),/;
    var srvendp = CONSTS.server_endpoint;

    this.update = function() {
        return $http.get(srvendp + "/configurations").then(function(response) {
            var path;
            me.configurations = response.data;
            me.paths = [];
            for (path in response.data) {
                if (response.data.hasOwnProperty(path)) {
                    me.paths.push(path);
                }
            }
            return me.paths.slice(); //copy
        });
    };

    this.getVersion = function(path) {
        return me.configurations[path].version;
    };

    this.get = function(path) {
        return me.configurations[path]; // ORIGINAL OBJECT
    };

    this.path2URI = function(path) {
        var cfg = me.configurations[path];
        return "http://" + cfg.host + ":" + cfg.port + cfg.urn;
    };

    this.URI2path = function(uri) {
        return RE_FULPATH.exec(uri)[1];
    };

    this.getPaths = function() {
        return me.paths.slice(); //copy
    };

    this.getConfigurations = function() {
        return JSON.parse(JSON.stringify(me.configurations)); // copy
    };

}]);
