/* jshint esnext: true */
angular.module("web-config").controller("ResponseInfoModalCtrl", ["$uibModalInstance", "$scope", function($uibModalInstance, $scope) {

    var me = this;
    this.info = null;

    this.close = function() {
        $uibModalInstance.dismiss('cancel');
    };

    function setInfo(response) {
        me.info = response;
    }

    $scope.request.then(setInfo).catch(setInfo);
    $scope.$on("modal.closing", function(event) {
        if (me.info === null) {
            event.preventDefault();
        }
    });
}]);
