<%! from nextgisweb.oapifserver.util import _ %>

<%inherit file="nextgisweb:resource/template/section_api.mako"/>

<%block name="content">
<% url_oapif = request.route_url('oapifserver.landing_page', id=obj.id) %>
<% external_doc_enabled = request.env.pyramid.options['nextgis_external_docs_links'] %>

<div class="section-api-item"
     data-title="${tr(_('OGC API - Features (OAPIF)'))}"
     data-tooltip-text="${tr(_('OGC API Features provides API building blocks to create, modify and query features on the Web.'))}"
     data-url="${url_oapif}"
     data-external-doc-enabled="${external_doc_enabled}"
     data-external-doc-url="${tr(_('https://docs.nextgis.com/docs_ngweb/source/layers.html#oapif-service'))}"
     data-external-doc-text="${tr(_('Read more'))}">
</div>
</%block>