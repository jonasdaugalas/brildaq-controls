angular.module("web-config").directive("wcAlerts", ["Alerts", "CONST", function(Alerts, CONST) {
    return {
        restrict: "E",
        templateUrl: "templates/alerts.html?" + APP_TIME,
        scope: true,
        controller: function() {
            var me = this;
            this.clientname = "";
            this.alerts = Alerts.alerts;

            this.close = function(item) {
                console.log("in remove", item);
                Alerts.remove(item);
            };

            this.doFullReload = function() {
                window.location.reload(true);
            };

            this.setClientNameCookie = function(provided) {
                var d = new Date();
                d.setTime(d.getTime() + (300*24*60*60*1000)); // 300 days
                var expires = "expires="+ d.toUTCString();
                var cookie = "clientname=";
                var srvendp = CONST.server_endpoint;
                if (provided) {
                    cookie += me.clientname.substring(0, 16);
                } else {
                    cookie += "client" +  Date.now().toString().substring(6, 10);
                }
                cookie += "; " + expires;
                console.log(cookie);
                document.cookie = cookie;
                cookie += ";path=" + srvendp;
                console.log(cookie);
                document.cookie = cookie;
            };
        },
        controllerAs: "ctrl"
    };
}]);
