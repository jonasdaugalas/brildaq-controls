angular.module("web-config").service("Alerts", ["Timers", function(Timers) {

    var me = this;
    this.alerts = [];

    this.alertByTypeExists = function(type) {
        var alert;
        for (alert of me.alerts) {
            if (alert.what === type) {
                return true;
            }
        }
        return false;
    };

    this.remove = function(item) {
        console.log("in remove", item);
        if (item.hasOwnProperty("timer")) {
            Timers.remove(item.timer);
        }
        var index = me.alerts.indexOf(item);
        me.alerts.splice(index, 1);
    };

    this.clear = function() {
        while (me.alerts.length > 0) {
            me.remove(me.alerts[0]);
        }
    };

    this.pushReloadAlert = function() {
        var timer = Timers.create(1000);
        var alert = {what: "reload", time: 30, timer: timer};
        timer.addAction({callable: function() {
            console.log('in action');
            if (alert.time > 0) {
                alert.time -= 1;
            } else {
                Timers.remove(alert.timer);
                console.log("timer ended. reloading.");
                window.location.reload(true);
            }
        }});
        me.alerts.push(alert);
    };

    this.pushNameAlert = function() {
        if (me.alertByTypeExists("name")) {
            return;
        }
        me.alerts.push({what: "name"});
    };

}]);
