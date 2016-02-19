angular.module("web-config").controller("MainCtrl", ["$rootScope", "Timers", function($rootScope, Timers) {

    var me = this;

    $rootScope.$on('$stateChangeStart', function(){
        Timers.clear();
    });

}]);
