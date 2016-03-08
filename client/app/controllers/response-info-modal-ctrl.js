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

    if (typeof $scope.requestPromise.then === "function") {

        $scope.requestPromise.then(function(response) {
            console.log(response);
            if ($scope.insteadResolve) {
                me.info = true;
                $uibModalInstance.close(response);
            } else {
                setInfo(response);
            }
        }).catch(function(response) {
            if ($scope.insteadReject) {
                me.info = "rejecting"; // to allow closing
                $uibModalInstance.dismiss(response);
            } else {
                setInfo(response);
            }
        });
    } else {
        setInfo($scope.requestPromise);
    }

    $scope.$on("modal.closing", function(event) {
        if (me.info === null) {
            event.preventDefault();
        }
    });
}]);
