require("./node_modules/angular/angular");
require("./node_modules/angular-ui-router/release/angular-ui-router.min");
require("./node_modules/angular-ui-bootstrap/dist/ui-bootstrap");
require("./node_modules/angular-ui-bootstrap/dist/ui-bootstrap-tpls");

require("./node_modules/ace-builds/src-min/ace");
require("./node_modules/ace-builds/src-min/mode-xml");
require("./node_modules/ace-builds/src-min/ext-searchbox");
require("./node_modules/ace-builds/src-min/ext-keybinding_menu");
require("./node_modules/angular-ui-ace/src/ui-ace");
require("./node_modules/angular-pretty-xml/dist/angular-pretty-xml");

require("./app/app");
require("./app/controllers/main-ctrl");
require("./app/controllers/overview-ctrl");
require("./app/controllers/editor-ctrl");
require("./app/controllers/view-xml-modal-ctrl");
require("./app/controllers/submit-modal-ctrl");
require("./app/controllers/response-info-modal-ctrl");
require("./app/services/configurations");
require("./app/services/wc-modals");
require("./app/services/alerts");
require("./app/services/timers");
require("./app/directives/view-fields");
require("./app/directives/edit-fields");
require("./app/directives/executive-info");
require("./app/directives/alerts");
