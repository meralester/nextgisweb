define([
    "dojo/_base/declare",
    "dojo/_base/lang",
    "dojo/request/xhr",
    "ngw/route",
    "dijit/_WidgetBase",
    "dijit/_TemplatedMixin",
    "dijit/_WidgetsInTemplateMixin",
    "ngw-resource/serialize",
    "dijit/form/CheckBox",
    "@nextgisweb/pyramid/i18n!",
    "@nextgisweb/pyramid/settings!",
    // resource
    "dojo/text!./OtherSettings.hbs",
    // template
    "dijit/form/Select",
    "dojox/layout/TableContainer",
], function (
    declare,
    lang,
    xhr,
    route,
    _WidgetBase,
    _TemplatedMixin,
    _WidgetsInTemplateMixin,
    serialize,
    CheckBox,
    i18n,
    settingsWebmap,
    template,
    Select
) {
    return declare(
        [
            _WidgetBase,
            serialize.Mixin,
            _TemplatedMixin,
            _WidgetsInTemplateMixin,
        ],
        {
            title: i18n.gettext("Settings"),
            templateString: i18n.renderTemplate(template),
            serializePrefix: "webmap",

            postCreate: function () {
                this.inherited(arguments);

                this._buildLegendSelect();
                if (settingsWebmap.annotation) this._buildAnnotationsControls();
            },
            
            _buildLegendSelect: function () {
                this.selLegend = new Select({
                    title: i18n.gettext("Show legend"),
                    options: [
                        {label: i18n.gettext("Default"), value: "default"},
                        {label: i18n.gettext("Yes"), value: "on"},
                        {label: i18n.gettext("No"), value: "off"},
                    ]
                });
                this.tcControls.addChild(this.selLegend);
            },

            _buildAnnotationsControls: function () {
                this.chbAnnotationEnabled = new CheckBox({
                    title: i18n.gettext("Enable annotations"),
                });
                this.selAnnotationDefault = new Select({
                    title: i18n.gettext("Show annotations"),
                    options: [
                        {label: i18n.gettext("No"), value: "no"},
                        {label: i18n.gettext("Yes"), value: "yes"},
                        {label: i18n.gettext("With messages"), value: "messages"},
                    ]
                });

                this.tcControls.addChild(this.chbAnnotationEnabled);
                this.tcControls.addChild(this.selAnnotationDefault);
            },

            serializeInMixin: function (data) {
                if (data.webmap === undefined) {
                    data.webmap = {};
                }
                var value = data.webmap;
                value.editable = this.chbEditable.get("checked");
                value.legend_visible = this.selLegend.get("value");

                if (settingsWebmap.annotation) {
                    value.annotation_enabled = this.chbAnnotationEnabled.get("checked");
                    value.annotation_default = this.selAnnotationDefault.get("value");
                }
            },

            deserializeInMixin: function (data) {
                var value = data.webmap;
                this.chbEditable.set("checked", value.editable);
                this.selLegend.set("value", value.legend_visible);

                if (settingsWebmap.annotation) {
                    this.chbAnnotationEnabled.set(
                        "checked",
                        value.annotation_enabled
                    );
                    this.selAnnotationDefault.set(
                        "value",
                        value.annotation_default
                    );
                }
            },
        }
    );
});
