var retry=0;

function checkReport(retry_num) {
    //If exists returns data, otherwise returns False
    var id = $('#reportKey').val();

    if (id){
        $.ajax({
           url: '/reports/check/'+id+'/?retry='+retry_num,
           success: writeReport
        });
    }
}

function writeReport(report) {
    if (report.data == 'none') {
        retry++;
        setTimeout('checkReport('+retry+')', 2500);
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
        'aoColumnDefs': [
            {
                'asSorting': ['desc', 'asc'],
                'aTargets': [0,1,2,3,4]
            }
        ],
        "aaSorting": [[ 1, 'asc' ]]
    });
}

$(document).ready(checkReport(retry));
