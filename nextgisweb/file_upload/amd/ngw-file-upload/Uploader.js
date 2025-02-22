define([
    "dojo/_base/declare",
    "dojo/Deferred",
    "dojo/dom-class",
    "dijit/_WidgetBase",
    "dijit/_TemplatedMixin",
    "dijit/_WidgetsInTemplateMixin",
    "@nextgisweb/pyramid/api",
    "@nextgisweb/pyramid/settings!",
    "@nextgisweb/pyramid/i18n!",
    "ngw-pyramid/ErrorDialog/ErrorDialog",
    "dojo/text!./template/Uploader.hbs",
    "./FileUploader",
    //
    "xstyle/css!./resource/Uploader.css",
], function (
    declare,
    Deferred,
    domClass,
    _WidgetBase,
    _TemplatedMixin,
    _WidgetsInTemplateMixin,
    api,
    settings,
    i18n,
    ErrorDialog,
    template,
    Uploader
) {
    function readableFileSize(size) {
        var units = ["B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB"];
        var i = 0;
        while (size >= 1024) {
            size /= 1024;
            ++i;
        }
        return size.toFixed(1) + " " + units[i];
    }

    return declare([_WidgetBase, _TemplatedMixin, _WidgetsInTemplateMixin], {
        templateString: i18n.renderTemplate(template),

        showProgressInDocTitle: true,
        uploaderLinkText: "",
        uploaderHelpText: "",
        stateClasses: ["uploader--start", "uploader--progress", "uploader--complete", "uploader--error"],

        constructor: function () {
            this.upload_promise = undefined;
            this.docTitle = document.title;
            this._accept = '';
        },
        postCreate: function () {
            this.uploaderWidget = new Uploader({
                label: i18n.gettext("Select"),
                multiple: false,
                uploadOnSelect: true,
                url: api.routeURL('file_upload.collection'),
                name: "file"
            }).placeAt(this.fileUploader);

            // Keep accept on reset
            this.connect(this.uploaderWidget, '_createInput', this._setAccept);

            var widget = this;
            this.uploaderWidget.on("begin", function () { widget.uploadBegin(); });
            this.uploaderWidget.on("progress", function (evt) { widget.uploadProgress(evt); });
            this.uploaderWidget.on("complete", function (data) { widget.uploadComplete(data); });
            this.uploaderWidget.on("error", this.uploadError.bind(this));

            widget.dndInit();
        },

        startup: function () {
            this.inherited(arguments);
            this.uploaderWidget.startup();
        },

        dndInit: function(){
            var dropTarget = this.dropTarget;

            this.uploaderWidget.addDropTarget(dropTarget);
            if (this.uploaderLinkText.length) this.fileLink.innerHTML = this.uploaderLinkText;
            if (this.uploaderHelpText.length) this.fileHelp.innerHTML = this.uploaderHelpText;
            this.maxSize.innerHTML = readableFileSize(settings.max_size) + " " + i18n.gettext("max");

            function dragOver(){
                domClass.add(dropTarget, "uploader__dropzone--active");
            }

            function dragLeave(){
                domClass.remove(dropTarget, "uploader__dropzone--active");
            }

            dropTarget.ondragover = dragOver;
            dropTarget.ondragleave = dragLeave;
            dropTarget.ondrop = dragLeave;
        },

        setAccept: function (accept) {
            this._accept = accept;
            this._setAccept();
        },

        _setAccept: function () {
            this.uploaderWidget.inputNode.accept = this._accept;
        },

        uploadBegin: function () {
            this.upload_promise = new Deferred();
            this.uploading = true;
            this.data = undefined;
            this.fileInfo.innerHTML = i18n.gettext("Uploading...");

            domClass.remove(this.focusNode, this.stateClasses);
            domClass.add(this.focusNode, "uploader--progress");
        },

        uploadProgress: function (evt) {
            if (evt.type === "progress") {
                this.fileInfo.innerHTML = evt.percent + i18n.gettext(" uploaded...");

                if (this.showProgressInDocTitle) {
                    document.title = evt.percent + " | " + this.docTitle;
                }
            }
        },

        uploadComplete: function (data) {
            this.upload_promise.resolve(data);
            this.uploading = false;

            // As this widget is used to upload individual
            // files, extract first element from the list
            this.data = data.upload_meta[0];
            this.fileInfo.innerHTML = this.data.name + " (" + readableFileSize(this.data.size) + ")";

            // Change text for choosing file
            domClass.remove(this.focusNode, this.stateClasses);
            domClass.add(this.focusNode, "uploader--complete");

            this.emit("complete");
        },

        uploadError: function (error) {
            this.upload_promise.reject(error);
            this.uploading = false;
            this.data = undefined;
            this.fileInfo.innerHTML = i18n.gettext("Could not load file!");

            domClass.remove(this.focusNode, this.stateClasses);
            domClass.add(this.focusNode, "uploader--error");

            // ErrorDialog have wrong behaviour with Error instances
            if (error instanceof Error) {
                error = Object.assign({}, error);
            }
            new ErrorDialog(error).show()
        },

        uploadReset: function() {
            this.uploading = false;
            this.data = undefined;
            this.fileInfo.innerHTML = "";
            domClass.remove(this.focusNode, this.stateClasses);
            domClass.add(this.focusNode, "uploader--start");
        },

        _getValueAttr: function () {
            var result;

            if (this.upload_promise === undefined || this.upload_promise.isResolved()) {
                result = this.data;
            } else {
                result = this.upload_promise;
            }

            return result;
        }
    });
});
