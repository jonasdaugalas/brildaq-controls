/* jshint esnext: true */
angular.module("web-config").controller("ViewXmlModalCtrl", ["$filter", "$uibModalInstance", "xml", "title", function($filter, $uibModalInstance,  xml, title) {

    var me = this;
    this.xml = xml;
    this.title = title;

    var editor;

    this.aceLoaded = function(_editor) {
        editor = _editor;
        editor.getSession().setUseWorker(false);
        editor.$blockScrolling = Infinity;
        editor.getSession().setUseSoftTabs(true);
        editor.setReadOnly(true);
        // editor.setKeyboardHandler("ace/keyboard/emacs");
        editor.setValue(me.xml);
    };

    this.beautify = function() {
        var text = editor.getValue();
        text = $filter("prettyXml")(text);
        editor.setValue(text);
    };

    this.close = function() {
        $uibModalInstance.dismiss('cancel');
    };

}]);
