define([
    "dojo/_base/declare",
    "dijit/_WidgetBase",
    "dijit/_TemplatedMixin",
    "dijit/_WidgetsInTemplateMixin",
    "dojo/text!./TinyDisplay.hbs",
    "dojo/_base/lang",
    "dojo/_base/array",
    "dojo/Deferred",
    "dojo/promise/all",
    "dojo/number",
    "dojo/aspect",
    "dojo/io-query",
    "dojo/dom-construct",
    "openlayers/ol",
    "ngw-webmap/ol/Map",
    "dijit/registry",
    "dijit/layout/ContentPane",
    "dijit/form/ToggleButton",
    "dijit/Dialog",
    "dojo/dom-style",
    "dojo/store/JsonRest",
    "dojo/request/xhr",
    "dojo/data/ItemFileWriteStore",
    "dojo/topic",
    "ngw/route",
    "@nextgisweb/pyramid/i18n!",
    "@nextgisweb/gui/error",
    "@nextgisweb/pyramid/icon",
    "ngw-pyramid/company-logo/company-logo",
    // tools
    "../../tool/Base",
    "../../tool/Zoom",
    "../../tool/Measure",
    "../../tool/Identify",
    "ngw-webmap/MapStatesObserver",
    "ngw-webmap/FeatureHighlighter",
    // settings
    "@nextgisweb/pyramid/settings!",
    "ngw-webmap/controls/LinkToMainMap",
    "dijit/layout/TabContainer",
    "dijit/layout/BorderContainer",
    "dijit/layout/ContentPane",
    "dojox/layout/TableContainer",
    // css
    "xstyle/css!../../template/resources/Display.css",
    "xstyle/css!./TinyDisplay.css"
], function (
    declare,
    _WidgetBase,
    _TemplatedMixin,
    _WidgetsInTemplateMixin,
    template,
    lang,
    array,
    Deferred,
    all,
    number,
    aspect,
    ioQuery,
    domConstruct,
    ol,
    Map,
    registry,
    ContentPane,
    ToggleButton,
    Dialog,
    domStyle,
    JsonRest,
    xhr,
    ItemFileWriteStore,
    topic,
    route,
    i18n,
    errorModule,
    icon,
    companyLogo,
    ToolBase,
    ToolZoom,
    ToolMeasure,
    Identify,
    MapStatesObserver,
    FeatureHighlighter,
    clientSettings,
    LinkToMainMap
) {

    var CustomItemFileWriteStore = declare([ItemFileWriteStore], {
        dumpItem: function (item) {
            var obj = {};

            if (item) {
                var attributes = this.getAttributes(item);

                if (attributes && attributes.length > 0) {
                    var i;

                    for (i = 0; i < attributes.length; i++) {
                        var values = this.getValues(item, attributes[i]);

                        if (values) {
                            if (values.length > 1) {
                                var j;

                                obj[attributes[i]] = [];
                                for (j = 0; j < values.length; j++) {
                                    var value = values[j];

                                    if (this.isItem(value)) {
                                        obj[attributes[i]].push(this.dumpItem(value));
                                    } else {
                                        obj[attributes[i]].push(value);
                                    }
                                }
                            } else {
                                if (this.isItem(values[0])) {
                                    obj[attributes[i]] = this.dumpItem(values[0]);
                                } else {
                                    obj[attributes[i]] = values[0];
                                }
                            }
                        }
                    }
                }
            }

            return obj;
        }
    });

    var LoggedDeferred = declare(Deferred, {
        constructor: function (name) {
            this.then(
                function () {
                    console.log("Deferred object [%s] resolved", name);
                },
                function () {
                    console.error("Deferred object [%s] rejected", name);
                }
            );
        }
    });

    return declare([_WidgetBase, _TemplatedMixin, _WidgetsInTemplateMixin], {
        templateString: i18n.renderTemplate(template),

        // AMD module loading: adapter, basemap, plugin
        _midDeferred: undefined,

        _itemStoreDeferred: undefined,
        _mapDeferred: undefined,
        _layersDeferred: undefined,
        _postCreateDeferred: undefined,
        _startupDeferred: undefined,

        // Permalink params
        _urlParams: undefined,

        // Current basemap
        _baseLayer: undefined,
        
        tiny: true,

        // For image loading
        assetUrl: ngwConfig.assetUrl,

        constructor: function (options) {
            declare.safeMixin(this, options);

            this._urlParams = (function(){
                var url, query, queryObject;
                url = window.location.toString();
                if (url.indexOf("?") !== -1) {
                    query = url.substring(url.indexOf("?") + 1, url.length);
                    queryObject = ioQuery.queryToObject(query);
                    if (lang.isString(queryObject.styles)) {
                        queryObject.styles = queryObject.styles.split(",");
                        queryObject.styles = array.map(queryObject.styles, function(i){ return parseInt(i, 10); });
                    }
                    return queryObject;
                }
                return {};
            })();

            this._itemStoreDeferred = new LoggedDeferred("_itemStoreDeferred");
            this._mapDeferred = new LoggedDeferred("_mapDeferred");
            this._layersDeferred = new LoggedDeferred("_layersDeferred");
            this._postCreateDeferred = new LoggedDeferred("_postCreateDeferred");
            this._startupDeferred = new LoggedDeferred("_startupDeferred");

            var widget = this;

            // AMD module loading
            this._midDeferred = {};
            this._mid = {};
            var mids = this.config.mid;

            this.clientSettings = clientSettings;

            // Add basemap's AMD modules
            mids.basemap.push(
                "ngw-webmap/ol/layer/OSM",
                "ngw-webmap/ol/layer/XYZ",
                "ngw-webmap/ol/layer/QuadKey"
            );

            array.forEach(Object.keys(mids), function (k) {
                var deferred = new LoggedDeferred("_midDeferred." + k);
                this._midDeferred[k] = deferred;

                var midarr = mids[k];
                require(midarr, function () {
                    var obj = {};
                    var i;
                    for (i = 0; i < arguments.length; i++) {
                        obj[midarr[i]] = arguments[i];
                    }

                    widget._mid[k] = obj;

                    deferred.resolve(obj);
                });
            }, this);

            // Map plugins
            var wmpmids = Object.keys(this.config.webmapPlugin);
            var deferred = new LoggedDeferred("_midDeferred.webmapPlugin");

            this._midDeferred.webmapPlugin = deferred;
            require(wmpmids, function () {
                var obj = {};
                for (var i = 0; i < arguments.length; i++) {
                    obj[wmpmids[i]] = arguments[i];
                }

                widget._mid.wmplugin = obj;

                deferred.resolve(obj);
            });

            this._itemStoreSetup();

            this._mapDeferred.then(
                function () { widget._itemStorePrepare(); }
            );

            this.displayProjection = "EPSG:3857";
            this.lonlatProjection = "EPSG:4326";

            if (this.config.extent[3] > 82) { this.config.extent[3] = 82; }
            if (this.config.extent[1] < -82) { this.config.extent[1] = -82; }

            this._extent = ol.proj.transformExtent(
                this.config.extent,
                this.lonlatProjection,
                this.displayProjection
            );

            all([this._layersDeferred, this._postCreateDeferred]).then(
                lang.hitch(this, function () {
                    var featureHighlighter = new FeatureHighlighter(this.map),
                        featureHighlighterPromise,
                        extent;

                    if (this._urlParams.feature_id && this._urlParams.layer_id) {
                        featureHighlighterPromise = featureHighlighter.highlightFeatureById(
                            this._urlParams.feature_id,
                            this._urlParams.layer_id
                        );

                        if (this._urlParams.zoom_to === 'true') {
                            featureHighlighterPromise.then(lang.hitch(this, function (feature) {
                                extent = feature.getGeometry().getExtent();
                                this.map.olMap.getView().fit(extent);
                            }));
                        }
                    }

                })
            ).then(undefined, function (err) { console.error(err); });

            // TODO: Remove useless code
            this._postCreateDeferred.then(
                function () {
                    //widget.loadBookmarks();
                }
            ).then(undefined, function (err) { console.error(err); });

            // Map and plugins
            all([this._midDeferred.basemap, this._midDeferred.webmapPlugin, this._startupDeferred]).then(
                function () {
                    widget._pluginsSetup(true);
                    widget._mapSetup();
                }
            ).then(undefined, function (err) {
                console.error(err);
            });

            all([this._mapDeferred, this._postCreateDeferred]).then(
               function () {
                   var baseLayerKey = widget._urlParams.base || 'osm-mapnik';

                   array.forEach(Object.keys(widget.map.layers), function (key) {
                       var layer = widget.map.layers[key];
                       if (!layer.isBaseLayer) return false;
                       if (key === baseLayerKey) {
                           widget.map.layers[key].olLayer.setVisible(true);
                           widget._baseLayer = widget.map.layers[key];
                       } else {
                           widget.map.layers[key].olLayer.setVisible(false);
                       }
                   });
               }
            ).then(undefined, function (err) { console.error(err); });

            // Setup layers
            all([this._midDeferred.adapter, this._itemStoreDeferred]).then(
                function () {
                    widget._layersSetup();
                }
            ).then(undefined, function (err) { console.error(err); });

            all([this._layersDeferred, this._mapSetup]).then(
                function () {
                    widget._mapAddLayers();

                    // Bind checkboxes and layer visibility
                    var store = widget.itemStore;
                    store.on("Set", function (item, attr, oldVal, newVal) {
                        if (attr === "checked" && store.getValue(item, "type") === "layer") {
                            var id = store.getValue(item, "id");
                            var layer = widget._layers[id];
                            layer.set("visibility", newVal);
                        }
                    });
                }
            ).then(undefined, function (err) { console.error(err); });


            // Tools and plugins
            all([this._midDeferred.plugin, this._layersDeferred]).then(
                function () {
                    widget._toolsSetup();
                    widget._pluginsSetup();
                    widget._identifyFeatureByAttrValue();
                }
            ).then(undefined, function (err) { console.error(err); });
            this.tools = [];
        },

        postCreate: function () {
            this.inherited(arguments);
            this._postCreateDeferred.resolve();
        },

        startup: function () {
            this.inherited(arguments);
            this._startupDeferred.resolve();
        },

        loadBookmarks: function () {
            if (this.config.bookmarkLayerId) {
                var store = new JsonRest({target: route.feature_layer.store({
                    id: this.config.bookmarkLayerId
                })});

                var display = this;

                store.query().then(
                    function (data) {
                        array.forEach(data, function (f) {
                            display.bookmarkMenu.addChild(new MenuItem({
                                label: f.label,
                                onClick: function () {
                                    // Request feature extent
                                    xhr.get(route.feature_layer.store.item({
                                        id: display.config.bookmarkLayerId,
                                        feature_id: f.id
                                    }), {
                                        handleAs: "json",
                                        headers: { "X-Feature-Box": true }
                                    }).then(
                                        function data(featuredata) {
                                            display.map.olMap.getView().fit(featuredata.box);
                                        }
                                    );
                                }
                            }));
                        });
                    }
                );
            } else {
                // Hide bookmarks button
                domStyle.set(this.bookmarkButton.domNode, "display", "none");
            }
        },

        _itemStoreSetup: function () {
            var itemConfigById = {};

            function prepare_item(item) {
                var copy = {
                    id: item.id,
                    type: item.type,
                    label: item.label
                };

                if (copy.type === "layer") {
                    copy.layerId = item.layerId;
                    copy.styleId = item.styleId;

                    copy.visibility = null;
                    copy.checked = item.visibility;
                    copy.position = item.drawOrderPosition;

                } else if (copy.type === "group" || copy.type === "root") {
                    copy.children = array.map(item.children, function (c) { return prepare_item(c); });
                }

                itemConfigById[item.id] = item;

                return copy;
            }

            var rootItem = prepare_item(this.config.rootItem);

            this.itemStore = new CustomItemFileWriteStore({data: {
                identifier: "id",
                label: "label",
                items: [ rootItem ]
            }});

            this._itemConfigById = itemConfigById;
        },

        _itemStorePrepare: function () {
            var widget = this;

            this.itemStore.fetch({
                queryOptions: { deep: true },
                onItem: function (item) {
                    widget._itemStorePrepareItem(item);
                },
                onComplete: function () {
                    widget.itemStore.on("Set", function (item, attr) {
                        if (attr === "checked") { widget._itemStoreVisibility(item); }
                    });

                    widget._itemStoreDeferred.resolve();
                },
                onError: function () {
                    widget._itemStoreDeferred.reject();
                }
            });
        },

        _itemStorePrepareItem: function (item) {
            this._itemStoreVisibility(item);
        },

        _itemStoreVisibility: function (item) {
            var store = this.itemStore;

            if (store.getValue(item, "type") === "layer") {
                var newVal = store.getValue(item, "checked");
                if (store.getValue(item, "visibility") !== newVal) {
                    console.log("Layer [%s] visibility has changed to [%s]", store.getValue(item, "id"), newVal);
                    store.setValue(item, "visibility", newVal);
                }
            }
        },

        _mapSetup: function () {
            var widget = this;

            this.map = new Map({
                target: this.mapNode,
                controls: [
                    new ol.control.Zoom({
                        zoomInLabel: domConstruct.create("span", {
                            class: "ol-control__icon",
                            innerHTML: icon.html({glyph: "add"})
                        }),
                        zoomOutLabel: domConstruct.create("span", {
                            class: "ol-control__icon",
                            innerHTML: icon.html({glyph: "remove"})
                        }),
                        zoomInTipLabel: i18n.gettext("Zoom in"),
                        zoomOutTipLabel: i18n.gettext("Zoom out"),
                        target: widget.leftTopControlPane,
                    }),
                    new ol.control.Attribution({
                        tipLabel: i18n.gettext("Attributions"),
                        target: widget.rightBottomControlPane,
                        collapsible: false
                    }),
                    new ol.control.ScaleLine({
                        target: widget.rightBottomControlPane,
                        minWidth: 48
                    }),
                    new ol.control.Rotate({
                        tipLabel: i18n.gettext("Reset rotation"),
                        target: widget.leftTopControlPane,
                        label: domConstruct.create("span", {
                            class: "ol-control__icon",
                            innerHTML: icon.html({glyph: "arrow_upward"})
                        })
                    }),
                ],
                view: new ol.View({
                    minZoom: 3,
                    constrainResolution: true
                })
            });

            if (this._urlParams.linkMainMap === 'true') {
                this.map.olMap.addControl(new LinkToMainMap({
                    url: mainDisplayUrl,
                    target: widget.leftBottomControlPane,
                    tipLabel: i18n.gettext('Open full map')
                }));
            }

            // Resize OpenLayers Map on container resize
            aspect.after(this.mapPane, "resize", function() {
                widget.map.olMap.updateSize();
            });

            // Basemaps initialization
            var idx = 0;
            array.forEach(clientSettings.basemaps, function (bm) {
                var MID = this._mid.basemap[bm.base.mid];

                var baseOptions = lang.clone(bm.base);
                var layerOptions = lang.clone(bm.layer);
                var sourceOptions = lang.clone(bm.source);

                if (baseOptions.keyname === undefined) {
                    baseOptions.keyname = "basemap_" + idx;
                }

                try {
                    var layer = new MID(baseOptions.keyname, layerOptions, sourceOptions);
                    if (layer.olLayer.getVisible()) {
                        this._baseLayer = layer;
                    }
                    layer.isBaseLayer = true;
                    this.map.addLayer(layer);
                } catch (err) {
                    console.warn("Can't initialize layer [" + baseOptions.keyname + "]: " + err);
                }

                idx = idx + 1;
            }, this);

            companyLogo(this.mapNode);

            this._setMapExtent();
            this._setBasemap();

            this._handlePostMessage();

            this._mapDeferred.resolve();
        },

        /**
         * Generate window `message` events to listen from iframe
         * @example
         * window.addEventListener('message', function(evt) {
         *    var data = evt.data;
         *    if (data.event === 'ngMapExtentChanged') {
         *        if (data.detail === 'zoom') {
         *        } else if (data.detail === 'move') {
         *        }
         *        // OR
         *        if (data.detail === 'position') {}
         *    }
         * }, false);
         */
        _handlePostMessage: function () {
            var widget = this;
            var parent = window.parent;
            if (this._urlParams.events === 'true' && parent && parent.postMessage) {
                var commonOptions = {
                    event: 'ngMapExtentChanged'
                };
                var parsePosition = function(pos) {
                    return {
                        zoom: pos.zoom,
                        lat: pos.center[1],
                        lon: pos.center[0]
                    }
                };
                widget.map.watch('position', function (name, oldPosition, newPosition) {
                    oldPosition = oldPosition ? parsePosition(oldPosition) : {};
                    newPosition = parsePosition(newPosition);
                    // set array of position part to compare between old and new state
                    var events = [
                        { params: ['lat', 'lon'], name: 'move' },
                        { params: ['zoom'], name: 'zoom' },
                    ];
                    var transformPosition = widget.map.getPosition(widget.lonlatProjection);
                    // prepare to send transform position
                    commonOptions.data = parsePosition(transformPosition);
                    array.forEach(events, function (event) {
                        var isChange = array.some(event.params, function (p) {
                            return oldPosition[p] !== newPosition[p];
                        });
                        if (isChange) {
                            commonOptions.detail = event.name;
                            // message should be a string to work correctly with all browsers and systems
                            parent.postMessage(JSON.stringify(commonOptions), '*');
                        }
                    });
                    // on any position change
                    commonOptions.detail = name;
                    parent.postMessage(JSON.stringify(commonOptions), '*');
                })
            }
        },

        _setMapExtent: function () {
            if (this._zoomByUrlParams()) return;
            this._zoomToInitialExtent();
        },
        
        _zoomByUrlParams: function () {
            const urlParams = this._urlParams;

            if (!("zoom" in urlParams && "lon" in urlParams && "lat" in urlParams)) {
                return false;
            }

            this.map.olMap.getView().setCenter(
                ol.proj.fromLonLat([
                    parseFloat(urlParams.lon),
                    parseFloat(urlParams.lat)
                ])
            );
            this.map.olMap.getView().setZoom(
                parseInt(urlParams.zoom)
            );

            if ("angle" in urlParams) {
                this.map.olMap.getView().setRotation(
                    parseFloat(urlParams.angle)
                );
            }
            
            return true;
        },

        _zoomToInitialExtent: function () {
            this.map.olMap.getView().fit(this._extent);
        },

        _identifyFeatureByAttrValue: function () {
            const urlParams = this._urlParams;

            if (!("hl_lid" in urlParams && "hl_attr" in urlParams && "hl_val" in urlParams)) {
                return;
            }
            
            this.identify
                .identifyFeatureByAttrValue(urlParams.hl_lid, urlParams.hl_attr, urlParams.hl_val)
                .then(result => {
                    if (result) return;
                    errorModule.errorModal({
                        title: i18n.gettext("Object not found"),
                        message: i18n.gettext("Object from URL parameters not found")
                    });
                });
        },

        _setBasemap: function () {
            var newBasemapKey = this._urlParams.base,
                newBasemapLayer,
                currentBasemapLayer;

            if (newBasemapKey) {
                if (this._baseLayer) {
                    currentBasemapLayer = this.map.layers[this._baseLayer.name];
                    currentBasemapLayer.olLayer.setVisible(false);
                }
                newBasemapLayer = this.map.layers[newBasemapKey];
                newBasemapLayer.olLayer.setVisible(true);
                this._baseLayer = newBasemapLayer;
            }
        },

        _mapAddLayers: function () {
            array.forEach(this._layer_order, function (id) {
                this.map.addLayer(this._layers[id]);
            }, this);
        },

        _adaptersSetup: function () {
            this._adapters = {};
            array.forEach(Object.keys(this._mid.adapter), function (k) {
                this._adapters[k] = new this._mid.adapter[k]({
                    display: this
                });
            }, this);
        },

        _layersSetup: function () {
            var widget = this,
                store = this.itemStore,
                layer;

            this._adaptersSetup();

            this._layers = {};              // Layer index by id
            this._layer_order = [];         // Layers from back to front

            // Layers initialization
            store.fetch({
                query: {type: "layer"},
                queryOptions: {deep: true},
                sort: widget.config.drawOrderEnabled ? [{
                    attribute: "position"
                }] : null,
                onItem: function (item) {
                    layer = widget._layerSetup(item);
                    widget._layer_order.unshift(store.getValue(item, "id"));
                    // Turn on layers from permalink
                    var cond,
                        visibleStyles = widget._urlParams.styles;
                    if (visibleStyles) {
                        cond = array.indexOf(visibleStyles, store.getValue(item, "styleId")) !== -1;
                        layer.olLayer.setVisible(cond);
                        layer.visibility = cond;
                        store.setValue(item, "checked", cond);
                    }
                },
                onComplete: function () {
                    widget._layersDeferred.resolve();
                },
                onError: function (error) {
                    console.error(error);
                    widget._layersDeferred.reject();
                }
            });
        },

        _layerSetup: function (item) {
            var store = this.itemStore;

            var data = this._itemConfigById[store.getValue(item, "id")];
            var adapter = this._adapters[data.adapter];

            data.minResolution = this.map.getResolutionForScale(
                data.maxScaleDenom,
                this.map.olMap.getView().getProjection().getMetersPerUnit()
            );
            data.maxResolution = this.map.getResolutionForScale(
                data.minScaleDenom,
                this.map.olMap.getView().getProjection().getMetersPerUnit()
            );

            var layer = adapter.createLayer(data);

            layer.itemId = data.id;
            layer.itemConfig = data;

            this._layers[data.id] = layer;
            return layer;
        },

        _toolsSetup: function () {
            var mapStates;

            this.identify = new Identify({display: this});
            mapStates = MapStatesObserver.getInstance();
            mapStates.addState('identifying', this.identify);
            mapStates.setDefaultState('identifying', true);

            topic.publish('/webmap/tools/initialized')
        },

        _pluginsSetup: function (wmplugin) {
            this._plugins = {};

            var widget = this,
                plugins = wmplugin ? this._mid.wmplugin
                                   : this._mid.plugin;

            array.forEach(Object.keys(plugins), function (key) {
                console.log("Plugin [%s]::constructor...", key);

                var plugin =  new plugins[key]({
                    identity: key,
                    display: this,
                    itemStore: wmplugin ? false : this.itemStore
                });

                widget._postCreateDeferred.then(
                    function () {
                        console.log("Plugin [%s]::postCreate...", key);
                        plugin.postCreate();

                        widget._startupDeferred.then(
                            function () {
                                console.log("Plugin [%s]::startup...", key);
                                plugin.startup();

                                widget._plugins[key] = plugin;
                                console.info("Plugin [%s] registered", key);
                            }
                        );
                    }
                );
            }, this);
        },

        getVisibleItems: function () {
            var store = this.itemStore,
                deferred = new Deferred();

            store.fetch({
                query: {type: "layer", visibility: "true"},
                sort: {attribute: "position"},
                queryOptions: {deep: true},
                onComplete: function (items) {
                    deferred.resolve(items);
                },
                onError: function (error) {
                    deferred.reject(error);
                }
            });

            return deferred;
        },

        dumpItem: function () {
            return this.itemStore.dumpItem(this.item);
        }
    });
});
