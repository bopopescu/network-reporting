(function () {

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
            window.retry++;
            setTimeout('checkReport(' + window.retry + ')', 2500);
            //setup another ajaxmagic
            return;
        }

        $('#preloader').hide();
        $('#table-goes-here').append(report.data);
        buildTable($('#report-table'));
    }

    function buildTable(table) {
        table.dataTable({
            bJQueryUI: true,
            aLengthMenu: [[50,100,-1], [50, 100, 'All']],
            iDisplayLength : 50,
            aoColumnDefs: [
                {
                    asSorting: ['desc', 'asc'],
                    aTargets: [0,1,2,3,4]
                }
            ],
            aaSorting: [[ 1, 'asc' ]]
        });
    }

    var ReportsController = {

        initializeReports: function () {
            window.retry = 0;
            checkReport(0);
        }
    };

    window.ReportsController = ReportsController;

})();
