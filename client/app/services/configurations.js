angular.module("web-config").service("Configurations", ["$http", "CONST", function($http, CONST) {

    var me = this;
    var RE_FULPATH = /.*?fullpath=(.*?),/;
    var srvendp = CONST.server_endpoint;
    var changingStates = ["GoingOn", "GoingOff", "Resetting"];

    var Configs = function(configs, whitelist, blacklist) {
        var path, cfg, uri;
        this.configs = {};
        this.uriToPath = {};
        this.pathToUri = {};
        console.log(configs, Object.keys(configs));
        for (path of Object.keys(configs)) {
            if (whitelist) {
                if (whitelist.indexOf(path) < 0) {
                    continue;
                }
            } else if (blacklist && blacklist.indexOf(path) >= 0) {
                continue;
            }
            cfg = configs[path];
            this.configs[path] = cfg;
            uri = "http://" + cfg.host + ":" + cfg.port + cfg.urn;
            this.uriToPath[uri] = path;
            this.pathToUri[path] = uri;
        }
        this.paths = Object.keys(this.configs);
    };

    Configs.prototype.getUris = function(paths) {
        var path, uris = [];
        for (path of paths) {
            uris.push(this.pathToUri[path]);
        }
        return uris;
    };

    Configs.prototype.getPaths = function(uris) {
        var uri, paths = [];
        for (uri of uris) {
            paths.push(this.uriToPath[uri]);
        }
        return paths;
    };

    Configs.prototype.pathKeys = function(data) {
        var uris = Object.keys(data);
        var uri, rekeyed = {};
        for (uri of uris) {
            rekeyed[this.uriToPath[uri]] = data[uri];
        }
        return rekeyed;
    };

    Configs.prototype.uriKeys = function(data) {
        var paths = Object.keys(data);
        var path, rekeyed = {};
        for (path of paths) {
            rekeyed[this.pathToUri[path]] = data[path];
        }
        return rekeyed;
    };

    var States = function(states) {
        var uri;
        this.states = states;
        this.active = [];
        this.uris = Object.keys(states);
        this.hasChangingStates = false;
        for (uri of this.uris) {
            if (this.states[uri] === "ON" ||
                this.states[uri] === "Error") {
                this.active.push(uri);
            }
            if (changingStates.indexOf(this.states[uri]) >= 0) {
                this.hasChangingStates = true;;
            }
        }
    };

    this.getConfigs = function(whitelist, blacklist) {
        return $http.get(srvendp + "/configurations").then(function(response) {
            return new Configs(response.data, whitelist, blacklist);
        }, handleServerError);
    };

    this.sendCommand = function(cmd, uri) {
        return $http.post(srvendp + "/send/" + cmd, JSON.stringify(uri))
            .catch(handleServerError);
    };

    this.create = function(uri) {
        return $http.post(srvendp + "/create", JSON.stringify(uri))
            .catch(handleServerError);
    };

    this.destroy = function(uri) {
        return $http.post(srvendp + "/destroy", JSON.stringify(uri))
            .catch(handleServerError);
    };

    this.getConfigDetails = function(path, version, withXml) {
        var url = srvendp + "/config" + path + "/v=" + version;
        if (!withXml) {
            url += '/noxml';
        }
        return $http.get(url).then(function(response) {
            return response.data;
        }, handleServerError);
    };

    this.getRunning = function(owner) {
        return $http.get(srvendp + "/running/" + owner)
            .then(function(response) {
                return response.data;
            }, handleServerError);
    };

    this.getStates = function(uris) {
        return $http.post(srvendp + "/states", uris).then(function(response) {
            return new States(response.data);
        }, handleServerError);
    };

    function handleServerError(response) {
        console.error(response);
        return Promise.reject(response);
    }
    // this.fetchVersions = function(path, older, from) {
    //     var requestURL = srvendp + "/history" + path;
    //     if (older) {
    //         if (from > 1) {
    //             requestURL += '/limit=20/bellow=' + from;
    //         } else {
    //             return Promise.reject(
    //                 "Not querying history, oldest version <= 1");
    //         }
    //     } else {
    //         requestURL += '/limit=20';
    //     }
    //     return $http.get(requestURL).then(function(response) {
    //         return response.data;
    //     }, function(response) {
    //         console.error("Failed to get versions for" + path);
    //         return Promise.reject();
    //     });
    // };

}]);
