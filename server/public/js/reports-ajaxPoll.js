function checkReport() {
    //If exists returns data, otherwise returns False
    //
    var id = $('#reportKey').val();
    $.ajax({
       url: '/reports/check/'+id+'/',
       success: writeReport,
       });
}

function writeReport(report) {
    if (report.data == 'none') {
        setTimeout('checkReport()', 2500);
        //setup another ajaxmagic
        return;
    }
    $('#preloader').hide();
    $('#table-goes-here').append(report.data);
    buildTable($('#report-table'));
}

function buildTable(table) {
    table.dataTable({
        'bJQueryUI':true,
        'aLengthMenu': [[50,100,-1], [50, 100, 'All']],
        'iDisplayLength' : 50,
        'aoColumnDefs': [ {'asSorting': ['desc', 'asc'], 'aTargets': [0,1,2,3,4]},]
    });
}

$(document).ready(checkReport());
