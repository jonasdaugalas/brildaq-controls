/* jshint esnext: true */
angular.module("web-config").controller("SubmitModalCtrl", ["$uibModalInstance", function($uibModalInstance) {

    var me = this;
    this.comment = "";

    this.confirm = function() {
        $uibModalInstance.close(me.comment);
    };

    this.close = function() {
        $uibModalInstance.dismiss('cancel');
    };

}]);
