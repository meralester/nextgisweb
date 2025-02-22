define([
    'dojo/_base/declare',
    'dojo/_base/lang',
    'dojo/dom-style',
    'dojo/on',
    'dijit/_WidgetBase',
    'dijit/form/ToggleButton',
    './controls/ToggleControl',
    'ngw/route',
    'ngw-webmap/MapStatesObserver',
    'dijit/ToolbarSeparator',
    'dijit/form/DropDownButton'
], function (
    declare,
    lang,
    domStyle,
    on,
    _WidgetBase,
    ToggleButton,
    ToggleControl,
    route,
    MapStatesObserver,
    ToolbarSeparator
) {
    return declare([_WidgetBase], {

        constructor: function (options) {
            this.display = options.display;
            this.mapStates = MapStatesObserver.getInstance();
        },

        addTool: function (tool, state, place) {
            place = place || this;
            
            const cssClasses = ["ol-control", "ol-unselectable"];
            if (tool.customCssClass) {
                cssClasses.push(tool.customCssClass);
            }

            var tglButtonTool = new ToggleControl({
                label: tool.label,
                showLabel: false,
                iconClass: tool.iconClass,
                tool: tool,
                state: state,
                intermediateChanges:false,
                customIcon: tool.customIcon,
                class: cssClasses.join(" ")
            });
            
            if (typeof place === "function") {
                place(tglButtonTool);
            } else {
                tglButtonTool.placeAt(place);
            }

            tool.toolbarBtn = tglButtonTool;
            this._bindChangeEvent(tglButtonTool);

            tglButtonTool.activate = lang.hitch(this, function () {
                this._unbindChangeEvent(tglButtonTool);
                tglButtonTool.set('checked', true);
                this._bindChangeEvent(tglButtonTool);
                tglButtonTool.tool.activate();
            });

            tglButtonTool.deactivate = lang.hitch(this, function () {
                this._unbindChangeEvent(tglButtonTool);
                tglButtonTool.set('checked', false);
                this._bindChangeEvent(tglButtonTool);
                tglButtonTool.tool.deactivate();
            });

            this.mapStates.addState(state, tglButtonTool, false);
        },

        _bindChangeEvent: function (tglButtonTool) {
            tglButtonTool._changeEventHandler = on(tglButtonTool, 'change', lang.hitch(this, function () {
                this._toolChangeEventHandle(tglButtonTool);
            }));
        },

        _unbindChangeEvent: function (tglButtonTool) {
            if (tglButtonTool._changeEventHandler) {
                tglButtonTool._changeEventHandler.remove();
                delete tglButtonTool._changeEventHandler;
            }
        },

        _toolChangeEventHandle: function (tglButtonTool) {
            var checked = tglButtonTool.get('checked');
            if (checked) {
                this.mapStates.activateState(tglButtonTool.state);
            } else {
                this.mapStates.deactivateState(tglButtonTool.state);
            }
        },

        addSeparator: function () {
            var toolbarSeparator = new ToolbarSeparator();
            toolbarSeparator.placeAt(this);
        },

        addButton: function (Button, options) {
            var button = new Button(options);
            button.display = this.display;
            button.placeAt(this);
        }
    });
});
