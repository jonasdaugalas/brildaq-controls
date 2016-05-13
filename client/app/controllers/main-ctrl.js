angular.module("web-config").controller("MainCtrl", ["$rootScope", "$http", "CONSTS", "Timers", function($rootScope, $http, CONSTS, Timers) {

    var me = this;

    // globals to be used by other controllers for global variables
    $rootScope.globals = {
        owner: "",
        app_time: APP_TIME
    };

    // load configuration constants
    $http.get("const.json?" + APP_TIME).then(function(response) {
        console.log(response);
        angular.copy(response.data, CONSTS);
        console.log(CONSTS);
        $rootScope.globals.owner = CONSTS.default_owner;
    });

    console.log('default owner', CONSTS.default_owner);
    console.log('owner', $rootScope.globals.owner);

    $rootScope.$on('$stateChangeStart', function(){
        Timers.clear();
    });

}]);
