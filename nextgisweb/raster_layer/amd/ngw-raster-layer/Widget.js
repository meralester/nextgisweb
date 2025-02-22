define([
    "dojo/_base/declare",
    "dijit/_WidgetBase",
    "dijit/_TemplatedMixin",
    "dijit/_WidgetsInTemplateMixin",
    "ngw-resource/serialize",
    "ngw-spatial-ref-sys/SRSSelect",
    "@nextgisweb/pyramid/i18n!",
    // resource
    "dojo/text!./template/Widget.hbs",
    // settings
    "@nextgisweb/pyramid/settings!",
    // template
    "dojox/layout/TableContainer",
    "dijit/form/CheckBox",
    "ngw-file-upload/Uploader"
], function (
    declare,
    _WidgetBase,
    _TemplatedMixin,
    _WidgetsInTemplateMixin,
    serialize,
    SRSSelect,
    i18n,
    template,
    settings
) {
    return declare("ngw.raster.layer.Widget", [_WidgetBase, serialize.Mixin, _TemplatedMixin, _WidgetsInTemplateMixin], {
        templateString: i18n.renderTemplate(template),
        title: i18n.gettext("Raster layer"),
        order: -50,
        activateOn: { create: true },
        prefix: "raster_layer",

        constructor: function () {
            this.wSrs = SRSSelect({allSrs: null});
        },

        postCreate: function () {
            this.inherited(arguments);

            this.wFile.on("begin", function () {
                this.resetSDN && this.resetSDN();
            }.bind(this));

            this.wFile.on("complete", function() {
                var fn = this.wFile.get("value").name;
                var we = fn.replace(/\.tiff?$/, '');
                if (fn != we) {
                    this.resetSDN = this.composite.suggestDN(we);
                }
            }.bind(this));

            this.wCOG.set("checked", settings.cog_enabled);
        },

        serialize: function(data, lunkwill) {
            this.inherited(arguments);

            var initial_cog_value = this.initial_cog_value;
            lunkwill.suggest(
                this.composite.operation == "create" ||
                  data.raster_layer.source !== undefined ||
                  data.raster_layer.cog !== initial_cog_value
              );
        },

        deserializeInMixin: function (data) {
            this.initial_cog_value = data.raster_layer.cog;
        },

        serializeInMixin: function (data) {
            if (data.raster_layer === undefined) { data.raster_layer = {}; }
            var value = data.raster_layer;
            
            value.srs = { id: this.wSrs.get("value") };
            value.source = this.wFile.data;
            value.cog = this.wCOG.checked;
        },

        validateDataInMixin: function (errback) {
            return this.composite.operation == "create" ?
                this.wFile.upload_promise !== undefined &&
                    this.wFile.upload_promise.isResolved() : true;
        }
    });
});
