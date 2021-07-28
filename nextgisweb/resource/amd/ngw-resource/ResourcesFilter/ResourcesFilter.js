define([
    "dojo/_base/declare", "dojo/_base/lang", "dojo/_base/array", "dojo/_base/Deferred",
    "dojo/on", "dojo/dom-class", "dojo/html", "dojo/query",
    "dojo/debounce", "dojo/request/xhr", "dojo/DeferredList",
    "dojox/dtl", "dojox/dtl/Context", "dijit/_WidgetBase", "dijit/_TemplatedMixin", "dijit/_WidgetsInTemplateMixin",
    "ngw/route", '@nextgisweb/pyramid/i18n!resource',
    "dojo/text!./ResourcesFilter.hbs", "dojo/text!./ResourcesFilterResult.dtl.hbs",
    "dojox/dtl/tag/logic",
    "xstyle/css!./ResourcesFilter.css",
    "dijit/form/TextBox"
], function (
    declare, lang, array, Deferred, on, domClass, html, query, debounce, xhr,
    DeferredList, dtl, dtlContext, _WidgetBase, _TemplatedMixin, _WidgetsInTemplateMixin,
    route, i18n, template, templateResult
) {
    var TEMPLATE_RESULT_DTL = new dtl.Template(templateResult),
        SVG_URL = ngwConfig.assetUrl + "/svg/svg-symbols.svg",
        translateDtl = {
            notFound: i18n.gettext("Resource not found")
        },
        resourceSearchRoute = route.resource.search,
        resourceShowRoute = route.resource.show;

    return declare([_WidgetBase, _TemplatedMixin, _WidgetsInTemplateMixin], {
        templateString: i18n.renderTemplate(template),
        title: i18n.gettext("Search resources"),

        postCreate: function () {
            var input = query('input', this.tbSearch.domNode)[0];
            on(input, "focus", lang.hitch(this, this.onFocusInput));
            on(input, "blur", lang.hitch(this, this.onBlurInput));

            on(this.tbSearch, "keyUp", debounce(lang.hitch(this, this.onChangeSearchInput), 1000));
        },

        getMinTimePromise: function (timeMs) {
            var deferred = new Deferred();
            setTimeout(function () {
                deferred.resolve();
            }, timeMs);
            return deferred;
        },

        onFocusInput: function () {
            domClass.add(this.domNode, "active");
        },

        onBlurInput: function () {
            domClass.remove(this.domNode, "active");
        },

        onChangeSearchInput: function () {
            var value = this.tbSearch.get("value");
            if (!value) return false;

            this.search(value);
        },

        search: function (value) {
            domClass.add(this.domNode, "loading");
            html.set(this.result, "");

            var deferredList = new DeferredList([
                this.getMinTimePromise(1000),
                xhr.get(resourceSearchRoute(), {
                    handleAs: "json",
                    query: {display_name: value}
                })
            ]);

            deferredList.then(
                lang.hitch(this, function (result) {
                    var searchResult = result[1];
                    if (searchResult[0]) {
                        this.onSearchSuccess(searchResult[1]);
                    } else {
                        this.onSearchFail(searchResult[1]);
                    }
                })
            );
        },

        onSearchSuccess: function (result) {
            var templateContext, resultHtml;

            result = array.map(result, function (item) {
                item.url = resourceShowRoute({id: item.resource.id});
                return item;
            }, this);

            templateContext = new dtlContext({
                svgUrl: SVG_URL,
                items: result,
                tr: translateDtl
            });
            resultHtml = TEMPLATE_RESULT_DTL.render(templateContext);
            html.set(this.result, resultHtml);

            domClass.remove(this.domNode, "loading");
        },

        onSearchFail: function (result) {
            domClass.remove(this.domNode, "loading");
            console.error(result);
        }
    });
});
