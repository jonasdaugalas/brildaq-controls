angular.module("web-config").controller("MainCtrl", ["$rootScope", "$http", "$stateParams", "CONST", "Timers", "Alerts", "config", function($rootScope, $http, $stateParams, CONST, Timers, Alerts, config) {

    var me = this;

    $rootScope.globals = {
        app_time: APP_TIME
    };

    console.log('Setting configuration from const.json');
    console.log(config);
    angular.copy(config.data, CONST); // fill CONST from const.json
    $rootScope.globals.owner = CONST.default_owner || "lumipro";
    $rootScope.globals.logs_endpoint = CONST.logs_endpoint || null;

    console.log('Setting profile');
    var p = $stateParams.profileName || "bril";
    p = p.split("/")[0];
    $rootScope.globals.profileName = p;
    $rootScope.globals.illegalProfile = !CONST.profiles.hasOwnProperty(p);

    console.log($stateParams);
    console.log($rootScope.globals);
    console.log(CONST);

    $rootScope.$on('$stateChangeStart', function(){
        Alerts.clear();
        Timers.clear();
    });

    window.onerror = function(msg, file, line, col, error) {
        console.log(msg, file, line, col, error);
    };
}]);
