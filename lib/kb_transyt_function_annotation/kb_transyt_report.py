from installed_clients.KBaseReportClient import KBaseReport
import uuid

search_bar_placeholder = "__SEARCHER__"


def generate_report(report_path, warnings, results, objects_created, callback_url, ws_name, genome_id,
                    file_path, html_template_path):

    report_params = {
        'warnings': warnings,
        'direct_html_link_index': 0,
        'workspace_name': ws_name,
        'report_object_name': 'run_transyt_annotation_' + uuid.uuid4().hex,
        'objects_created': objects_created,
    }

    if results is not None:
        generate_html_file(report_path, results, html_template_path)
        report_params['file_links'] = [{'name': genome_id + "tc_numbers.txt", 'description': 'desc', 'path': file_path}]
        report_params['html_links'] = [{'name': 'report', 'description': 'Report HTML', 'path': report_path}]

    report = KBaseReport(callback_url)
    report_info = report.create_extended_report(report_params)

    return report_info


def generate_html_file(report_path, results, html_template_path):

    onclick_bar = "<p></p><div class='tab'>\n"
    html = ""
    object_id = 1

    onclick_bar = onclick_bar + "<button class=\"tablinks\" onclick=\"openTab(event, 'TC number annotations')\"\
    id='defaultOpen'>TC number annotations</button>\n"
    html = html + "<div id=\"TC number annotations\" class=\"tabcontent\">"

    html = html + "<table id='myTable" + str(object_id) + "' class='tg'><thead><tr><h3>List of genes with new" \
                                                          " TC number annotations.</h3></tr>\n"
    html = html + search_bar_placeholder + "<tr><th class='tg-i1re'>Feature ID</th>\
    <th class='tg-i1re'>Annotation</th></tr></thead><tbody>"
    html = html + build_html_table(results)

    search_bar = "<input type='text' id='myInput" + str(object_id) + "' onkeyup='myFunction" + str(object_id)\
                 + "()' placeholder='Type a query to search in all columns' title='Type in a name'>\n"
    html = html.replace(search_bar_placeholder, search_bar)
    html = html + "</tbody></table></div>\n\n"

    object_id += 1

    search_style = get_search_bar_style(object_id)
    search_script = get_search_bar_script(object_id)

    onclick_bar = onclick_bar + "</div>"
    html = onclick_bar + html

    with open(report_path, 'w') as result_file:
        with open(html_template_path, 'r') as report_template_file:
            report_template = report_template_file.read()
            report_template = report_template.replace('#MY_INPUT', search_style)
            report_template = report_template.replace('#MY_SCRIPT', search_script)
            report_template = report_template.replace('<p>BODY_CONTENT</p>', html)
            result_file.write(report_template)


def build_html_table(results):
    html = ""

    for identifier in sorted(results):
        identifier = identifier.replace("_c0", "")

        html = html + "<tr>"
        html = html + "<td class='tg-baqh'>" + identifier + "</td>"
        html = html + "<td class='tg-0lax'>>" + "\n>".join(results[identifier]) + "</td>"
        html = html + "</tr>\n"

    return html



def get_search_bar_style(object_id):

    html = ""

    for i in range(1, object_id):
        if html:
            html = html + ", "
        html = html + "#myInput" + str(i)

    return html


def get_search_bar_script(object_id):

    html = "<script>"

    for i in range(1, object_id):
        html = html + "function myFunction" + str(i) + "() {\n var input, filter, table, tr, td, i, txtValue; " \
                                                       "input = document.getElementById(\"myInput" + str(i) + "\"); " \
                                                        "filter = input.value.toUpperCase(); " \
                                                        "table = document.getElementById(\"myTable" + str(i) + "\"); " \
                                                        "tr = table.getElementsByTagName(\"tr\"); " \
                                                        "th = table.getElementsByTagName(\"th\"); " \
                                                        "for (i = 0; i < tr.length; i++) " \
                                                        "for(j = 0; j < th.length; j++){ " \
                                                        "td = tr[i].getElementsByTagName(\"td\")[j]; " \
                                                        "if (td) { txtValue = td.textContent || td.innerText; " \
                                                        "if (txtValue.toUpperCase().indexOf(filter) > -1) {" \
                                                        "tr[i].style.display = \"\";break;}" \
                                                        "else {tr[i].style.display = \"none\";}}}}\n\n"

    return html + "</script>"
