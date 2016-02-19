angular.module("web-config").service("Timers", ["$timeout", "$interval", function($timeout, $interval) {
    var me = this;

    this.timers = [];

    var Timer = function(interval) {
        var actions = [];
        var handler = null;

        this.getIntervalValue = function() {
            return interval;
        };

        this.addAction = function(obj) {
            console.log("Binding action to timer");
            var index = actions.indexOf(obj);
            if (index < 0) {
                actions.push(obj);
            }
        };

        this.removeAction = function(obj) {
            console.log("Unbinding action from timer");
            var index = actions.indexOf(obj);
            while (index > -1) {
                actions.splice(index, 1);
                index = actions.indexOf(obj);
            }
        };

        this.stop = function() {
            console.log("Stopping timer. Actions:", actions);
            actions.length = 0;
            if (handler != null) {
                $interval.cancel(handler);
            }
        };

        handler = $interval(function() {
            var action;
            for (action of actions) {
                if ("callable" in action
                    && typeof action.callable === "function") {
                    //then
                    (function(fn) {
                        $timeout(fn);
                    })(action.callable);
                }
            }
        }, interval);
    };

    this.create = function(interval) {
        console.log("Creating timer", interval);
        if (isNaN(interval) || interval < 1) {
            return null;
        }
        var t = new Timer(interval);
        me.timers.push(t);
        return t;
    };

    this.remove = function(timer) {
        var index = me.timers.indexOf(timer);
        if (index < 0) {
            return false;
        }
        while (index > -1) {
            me.timers[index].stop();
            me.timers.splice(index, 1);
            index = me.timers.indexOf(timer);
        }
        return true;
    };

    this.clear = function() {
        console.log("Clearing timers.");
        for (var i = 0; i < me.timers.length; i++) {
            if (typeof me.timers[i].stop === "function") {
                me.timers[i].stop();
            }
        }
        me.timers.length = 0;
    };
}]);
