from collections import namedtuple
from urllib.parse import unquote, urljoin, urlparse

from pyramid.renderers import render_to_response

from ..render import ILegendSymbols

from .adapter import WebMapAdapter
from .model import WebMap, WebMapScope, WebMapItem
from .plugin import WebmapPlugin, WebmapLayerPlugin
from .util import webmap_items_to_tms_ids_list, _
from ..env import env
from ..lib.dynmenu import DynItem, Label, Link
from ..render.api import legend_symbols_by_resource
from ..resource import Resource, Widget, resource_factory, DataScope, ResourceScope
from ..pyramid import viewargs


class ExtentWidget(Widget):
    resource = WebMap
    operation = ('create', 'update')
    amdmod = 'ngw-webmap/ExtentWidget'


class ItemWidget(Widget):
    resource = WebMap
    operation = ('create', 'update')
    amdmod = 'ngw-webmap/ItemWidget'


class SettingsWidget(Widget):
    resource = WebMap
    operation = ('create', 'update')
    amdmod = 'ngw-webmap/resource/OtherSettings/OtherSettings'


@viewargs(renderer='react')
def settings(request):
    request.require_administrator()
    return dict(
        entrypoint='@nextgisweb/webmap/settings',
        title=_("Web map settings"),
        dynmenu=request.env.pyramid.control_panel)


def check_origin(request):
    if (
        not request.env.webmap.options['check_origin']
        or request.headers.get('Sec-Fetch-Dest') != 'iframe'
        or request.headers.get('Sec-Fetch-Site') == 'same-origin'
    ):
        return True

    referer = request.headers.get('Referer')
    if referer is not None:
        if referer.endswith('/'):
            referer = referer[:-1]
        if (
            not referer.startswith(request.application_url)
            and not request.check_origin(referer)
        ):
            webmap_url = request.route_url(
                'webmap.display',
                id=request.context.id
            ) + '?' + request.query_string

            response = render_to_response(
                'nextgisweb:webmap/template/invalid_origin.mako', dict(
                    origin=urljoin(request.headers.get('Referer'), '/'),
                    domain=urlparse(request.application_url).hostname,
                    webmap_url=webmap_url,
                ), request)
            response.status = 403
            return response

    return True


def get_legend_visible_default() -> str:
    webmaps_legend_setting = env.core.settings_get('webmap', 'legend_visible', 'default')
    if webmaps_legend_setting != 'default':
        legend_visible_default = webmaps_legend_setting
    else:
        config_legend_setting = env.webmap.options['legend_visible']
        legend_visible_default = 'on' if config_legend_setting else 'disabled'
    return legend_visible_default


def get_legend_info(webmap: WebMap, webmap_item: WebMapItem, style, visible_default: str):
    legend_visible = webmap_item.legend_visible

    if legend_visible == 'default':
        legend_visible = webmap.legend_visible if webmap.legend_visible != 'default' else visible_default

    legend_info = dict(visible=legend_visible)

    if legend_visible == 'on' or legend_visible == 'off':
        has_legend = ILegendSymbols.providedBy(style)
        legend_info.update(dict(has_legend=has_legend))
        if has_legend:
            legend_symbols = legend_symbols_by_resource(style, 15)
            legend_info.update(dict(symbols=legend_symbols))
            is_single = len(legend_symbols) == 1
            legend_info.update(dict(single=is_single))
            if not is_single:
                legend_info.update(dict(open=legend_visible == 'on'))

    return legend_info


@viewargs(renderer='mako')
def display(obj, request):
    is_valid_or_error = check_origin(request)
    if is_valid_or_error is not True:
        return is_valid_or_error

    request.resource_permission(WebMap.scope.webmap.display)

    MID = namedtuple('MID', ['adapter', 'basemap', 'plugin'])

    display.mid = MID(
        set(),
        set(),
        set(),
    )

    # Map level plugins
    plugin = dict()
    for pcls in WebmapPlugin.registry:
        p_mid_data = pcls.is_supported(obj)
        if p_mid_data:
            plugin.update((p_mid_data,))

    items_states = {
        'expanded': [],
        'checked': []
    }

    legend_visible_default = get_legend_visible_default()

    def traverse(item):
        data = dict(
            id=item.id,
            key=item.id,
            type=item.item_type,
            label=item.display_name,
            title=item.display_name,
        )

        if item.item_type == 'layer':
            style = item.style
            layer = style.parent

            if not style.has_permission(DataScope.read, request.user):
                return None

            # If there are no necessary permissions skip web-map element
            # so it won't be shown in the tree

            # TODO: Security

            # if not layer.has_permission(
            #     request.user,
            #     'style-read',
            #     'data-read',
            # ):
            #     return None

            layer_enabled = bool(item.layer_enabled)
            if layer_enabled:
                items_states.get('checked').append(item.id)

            # Main element parameters
            data.update(
                layerId=style.parent_id,
                styleId=style.id,
                visibility=layer_enabled,
                identifiable=item.layer_identifiable,
                transparency=item.layer_transparency,
                minScaleDenom=item.layer_min_scale_denom,
                maxScaleDenom=item.layer_max_scale_denom,
                drawOrderPosition=item.draw_order_position,
                legendInfo=get_legend_info(obj, item, style, legend_visible_default),
            )

            data['adapter'] = WebMapAdapter.registry.get(
                item.layer_adapter, 'image').mid
            display.mid.adapter.add(data['adapter'])

            # Layer level plugins
            plugin = dict()
            for pcls in WebmapLayerPlugin.registry:
                p_mid_data = pcls.is_layer_supported(layer, obj)
                if p_mid_data:
                    plugin.update((p_mid_data,))

            data.update(plugin=plugin)
            display.mid.plugin.update(plugin.keys())

        elif item.item_type in ('root', 'group'):
            expanded = item.group_expanded
            if expanded:
                items_states.get('expanded').append(item.id)
            # Recursively run all elements excluding those
            # with no permissions
            data.update(
                expanded=expanded,
                children=list(filter(
                    None,
                    map(traverse, item.children)
                ))
            )
            # Hide empty groups
            if (item.item_type in 'group') and not data['children']:
                return None

        return data

    tmp = obj.to_dict()

    display_config = dict(
        extent=tmp["extent"],
        extent_constrained=tmp["extent_constrained"],
        rootItem=traverse(obj.root_item),
        itemsStates=items_states,
        mid=dict(
            adapter=tuple(display.mid.adapter),
            basemap=tuple(display.mid.basemap),
            plugin=tuple(display.mid.plugin)
        ),
        webmapPlugin=plugin,
        bookmarkLayerId=obj.bookmark_resource_id,
        tinyDisplayUrl=request.route_url('webmap.display.tiny', id=obj.id),
        testEmbeddedMapUrl=request.route_url('webmap.preview_embedded', id=obj.id),
        webmapId=obj.id,
        webmapDescription=obj.description,
        webmapTitle=obj.display_name,
        webmapEditable=obj.editable,
        webmapLegendVisible=obj.legend_visible,
        drawOrderEnabled=obj.draw_order_enabled,
    )

    if request.env.webmap.options['annotation']:
        display_config['annotations'] = dict(
            enabled=obj.annotation_enabled,
            default=obj.annotation_default,
            scope=dict(
                read=obj.has_permission(WebMapScope.annotation_read, request.user),
                write=obj.has_permission(WebMapScope.annotation_write, request.user),
                manage=obj.has_permission(WebMapScope.annotation_manage, request.user),
            )
        )

    return dict(
        obj=obj,
        display_config=display_config,
        custom_layout=True
    )


@viewargs(renderer='mako')
def display_tiny(obj, request):
    return display(obj, request)


@viewargs(renderer='react')
def clone(request):
    request.resource_permission(ResourceScope.read)
    return dict(
        entrypoint='@nextgisweb/webmap/clone-webmap',
        props=dict(id=request.context.id),
        obj=request.context,
        title=_("Clone web map"))


@viewargs(renderer='mako')
def preview_embedded(request):
    iframe = request.POST['iframe']
    request.response.headerlist.append(("X-XSS-Protection", "0"))
    return dict(
        iframe=unquote(unquote(iframe)),
        title=_("Embedded webmap preview"),
        limit_width=False,
    )


def setup_pyramid(comp, config):
    config.add_route(
        'webmap.display', r'/resource/{id:\d+}/display',
        factory=resource_factory, client=('id', )
    ).add_view(display, context=WebMap)

    config.add_route(
        'webmap.display.tiny', r'/resource/{id:\d+}/display/tiny',
        factory=resource_factory, client=('id', )
    ).add_view(display_tiny, context=WebMap)

    config.add_route(
        'webmap.preview_embedded', '/webmap/embedded-preview'
    ).add_view(preview_embedded)

    config.add_route(
        'webmap.clone', r'/resource/{id:\d+}/clone',
        factory=resource_factory, client=('id',)
    ).add_view(clone, context=WebMap)

    class DisplayMenu(DynItem):
        def build(self, args):
            yield Label('webmap', _("Web map"))

            if isinstance(args.obj, WebMap):
                if args.obj.has_permission(WebMapScope.display, args.request.user):
                    yield Link(
                        'webmap/display', _("Display"), self._display_url(),
                        important=True, target='_blank',
                        icon='webmap-display')

                if args.obj.has_permission(ResourceScope.read, args.request.user):
                    yield Link(
                        'webmap/clone', _("Clone"), self._clone_url(),
                        important=False, target='_self',
                        icon='material-content_copy')

        def _display_url(self):
            return lambda args: args.request.route_url(
                'webmap.display', id=args.obj.id)

        def _clone_url(self):
            return lambda args: args.request.route_url(
                'webmap.clone', id=args.obj.id)

    WebMap.__dynmenu__.add(DisplayMenu())

    config.add_route(
        'webmap.control_panel.settings',
        '/control-panel/webmap-settings'
    ).add_view(settings)

    comp.env.pyramid.control_panel.add(
        Link('settings.webmap', _("Web map"), lambda args: (
            args.request.route_url('webmap.control_panel.settings'))))

    Resource.__psection__.register(
        key='description', title=_("External access"),
        is_applicable=lambda obj: obj.cls == 'webmap' and webmap_items_to_tms_ids_list(obj),
        template='section_api_webmap.mako')
