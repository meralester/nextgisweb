<%inherit file='nextgisweb:pyramid/template/base.mako' />
<%! from nextgisweb.pyramid.util import _ %>

<%def name="title_ext()">
    <div id="info-copy-btn" style="float: right"></div>
</%def>


<% distr_opts = request.env.options.with_prefix('distribution') %>
<% support_url = request.env.core.support_url_view(request) %>
%if distr_opts.get('name') is not None:
    <h2>${distr_opts.get('description')} ${distr_opts.get('version')} (${distr_opts.get('date')})</h2>
    %if request.env.ngupdate_url:
        <div id="updateSysInfo"></div>
        <script type="text/javascript">
            require([
                "@nextgisweb/pyramid/update/sysinfo",
                "@nextgisweb/gui/react-app"
            ], function (
                updateSysInfo, reactApp
            ) {
                reactApp.default(
                    updateSysInfo.default, {},
                    document.getElementById("updateSysInfo"),
                );
            });
        </script>
    %endif
%endif
<div class="content-box">
    <div class="table-wrapper">
        <table id="package-table" class="pure-table pure-table-horizontal">

            <thead><tr> 
                <th class="sort-default" style="width: 100%; text-align: inherit;">${tr(_('Package'))}</th>
                <th style="width: 8em; text-align: inherit;" colspan="2" data-sort-method='dotsep'>${tr(_('Version'))}</th>
            </tr></thead>

            <tbody>

            <%
                packages = list(request.env.packages.items())
                packages.sort(key=lambda i: '' if i[0] == 'nextgisweb' else i[0])
            %>
            
            %for pname, pobj in packages:
            <tr>
                <td><%
                    value = pobj.metadata['Summary']
                    if value == 'UNKNOWN':
                        value = None
                    if not value:
                        value = pobj.name
                %>${value}</td>
                <td>${pobj.version}</td>
                <td>
                    %if pobj.commit:
                        ${pobj.commit + ('+' if pobj.dirty else '')}
                    %else:
                        &nbsp;
                    %endif
                </td>
            </tr>
            %endfor

            </tbody>
        </table>
    </div>
</div>

<h2>${tr(_('Platform'))}</h2>

<div class="content-box"><div class="table-wrapper">
    <table id="package-table" class="pure-table pure-table-horizontal"><tbody>
    %for comp in request.env._components.values():
        %for k, v in comp.sys_info():
            <tr>
                <th>${tr(k)}</th>
                <td>${tr(v)}</td>
            </tr>
        %endfor
    %endfor
    </tbody> </table>
</div></div>


<script>
    require([
        "dojo/ready",
        "ngw-pyramid/CopyButton/CopyButton",
    ], function (
        ready, 
        CopyButton,
    ) {
        var domCopyButton = document.getElementById("info-copy-btn")
        var copyButton = new CopyButton({
            targetAttribute: function (target) {
                return document.getElementById("content-wrapper").innerText;
            }
        });
        copyButton.placeAt(domCopyButton);
    });
</script>
