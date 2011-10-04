class AdNetworkReportIndexHandler(RequestHandler):
    def get(self):
        manager = AdNetworkReportQueryManager(self.account)
        totals = manager.get_ad_network_totals()
        
        return render_to_response(self.request, 'ad_network_report/ad_network_index.html',
                dict(totals  = totals))
                     
@login_required
def report_index(request, *args, **kwargs):
    return AdNetworkReportIndexHandler()(request, *args, **kwargs)
     
class ViewAdNetworkReportHandler(RequestHandler):
    def get(self, ad_network_app_mapper_key, *args, **kwargs):
        manager = ReportQueryManager(self.account)
        stats = manager.get_ad_network_app_stats(ad_network_app_mapper)
        
        return render_to_response(self.request, 'ad_network_report/view_ad_network_report.html',
                dict(stats = report.most_recent))

@login_required
def view_report(request, *args, **kwargs):
    return ViewAdNetworkReportHandler()(request, *args, **kwargs)