angular.module("web-config").controller("MainCtrl", ["$rootScope", "CLIENT_CONSTS", "Timers", function($rootScope, CONSTS, Timers) {

    var me = this;

    // globals to be used by other controllers for global variables
    $rootScope.globals = {
        owner: CONSTS.default_owner
    };

    $rootScope.$on('$stateChangeStart', function(){
        Timers.clear();
    });

}]);
