angular.module("web-config").directive("wcEditFields", function() {
    return {
        restrict: "E",
        templateUrl: "templates/edit-fields.html?" + APP_TIME,
        bindToController: {
            fields: "="
        },
        scope: true,
        controller: function() {
            this.swap = function(arr, a, b) {
                var tmp = arr[a];
                arr[a] = arr[b];
                arr[b] = tmp;
            };

            this.delete = function(obj, key) {
                delete obj[key];
            };

            this.mapinsert = function(obj, key, val) {
                if (obj.hasOwnProperty(key)) {
                    return;
                }
                if (typeof key !== "string" || key === "") {
                    return;
                }
                obj[key] = val;
            };

            this.togleBool = function(field) {
                if (field.value === 'true') {
                    field.value = 'false';
                } else if (field.value === 1) {
                    field.value = 0;
                } else if (field.value === 0) {
                    field.value = 1;
                } else {
                    field.value = 'true';
                }
            };
        },
        controllerAs: "ctrl"
    };
});
