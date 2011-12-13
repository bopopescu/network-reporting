var retry=0;

function checkReport(retry_num) {
    //If exists returns data, otherwise returns False
    //
    var id = $('#reportKey').val();
    console.log($('#reportKey'));
    console.log($('#reportKey').val());
    console.log(id);

    $.ajax({
       url: '/reports/check/'+id+'/?retry='+retry_num,
       success: writeReport
    });
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
        "fnDrawCallback": function ( settings ) {
            if ( settings.aiDisplay.length == 0 )
            {
                return;
            }

            var table_rows = $('tbody tr', settings.nTable);
            var number_of_columns = table_rows[0].getElementsByTagName('td').length;
            var sLastGroup = "";
            for (var i=0; i < table_rows.length; i++)
            {
                var display_index = settings._iDisplayStart + i;
                var sGroup = settings.aoData[settings.aiDisplay[display_index]]._aData[0];
                if ( sGroup != sLastGroup )
                {
                    var nGroup = document.createElement( 'tr' );
                    var nCell = document.createElement( 'td' );
                    nCell.colSpan = number_of_columns;
                    nCell.className = "group";
                    nCell.innerHTML = sGroup;
                    nGroup.appendChild( nCell );
                    table_rows[i].parentNode.insertBefore( nGroup, table_rows[i] );
                    sLastGroup = sGroup;
                }
            }
        },
        "aaSorting": [[ 1, 'asc' ]]
    });
}

$(document).ready(checkReport(retry));
