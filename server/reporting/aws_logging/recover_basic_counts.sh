PATH=~/mopub/server/reporting/aws_logging:$PATH:/usr/local/bin:~/google_appengine
APP_DIR=~/mopub/server

START_TIME=$(date +%s)
python $APP_DIR/reporting/aws_logging/stats_updater.py -f ~/aws_logs/offline_recover/basic/aws-logfile-2011-0604-0000-full.basic.lc.stats -n 128
STOP_TIME=$(date +%s)
echo "0604:" $(((STOP_TIME-START_TIME)/60)) "minutes" >> ~/tmp/offline_basic_recover.log

START_TIME=$(date +%s)
python $APP_DIR/reporting/aws_logging/stats_updater.py -f ~/aws_logs/offline_recover/basic/aws-logfile-2011-0605-0000-full.basic.lc.stats -n 128
STOP_TIME=$(date +%s)
echo "0605:" $(((STOP_TIME-START_TIME)/60)) "minutes" >> ~/tmp/offline_basic_recover.log

START_TIME=$(date +%s)
python $APP_DIR/reporting/aws_logging/stats_updater.py -f ~/aws_logs/offline_recover/basic/aws-logfile-2011-0606-0000-full.basic.lc.stats -n 128
STOP_TIME=$(date +%s)
echo "0606:" $(((STOP_TIME-START_TIME)/60)) "minutes" >> ~/tmp/offline_basic_recover.log

START_TIME=$(date +%s)
python $APP_DIR/reporting/aws_logging/stats_updater.py -f ~/aws_logs/offline_recover/basic/aws-logfile-2011-0607-0000-full.basic.lc.stats -n 128
STOP_TIME=$(date +%s)
echo "0607:" $(((STOP_TIME-START_TIME)/60)) "minutes" >> ~/tmp/offline_basic_recover.log

START_TIME=$(date +%s)
python $APP_DIR/reporting/aws_logging/stats_updater.py -f ~/aws_logs/offline_recover/basic/aws-logfile-2011-0608-0000-full.basic.lc.stats -n 128
STOP_TIME=$(date +%s)
echo "0608:" $(((STOP_TIME-START_TIME)/60)) "minutes" >> ~/tmp/offline_basic_recover.log

START_TIME=$(date +%s)
python $APP_DIR/reporting/aws_logging/stats_updater.py -f ~/aws_logs/offline_recover/basic/aws-logfile-2011-0609-0000-full.basic.lc.stats -n 128
STOP_TIME=$(date +%s)
echo "0609:" $(((STOP_TIME-START_TIME)/60)) "minutes" >> ~/tmp/offline_basic_recover.log

START_TIME=$(date +%s)
python $APP_DIR/reporting/aws_logging/stats_updater.py -f ~/aws_logs/offline_recover/basic/aws-logfile-2011-0610-0000-full.basic.lc.stats -n 128
STOP_TIME=$(date +%s)
echo "0610:" $(((STOP_TIME-START_TIME)/60)) "minutes" >> ~/tmp/offline_basic_recover.log

START_TIME=$(date +%s)
python $APP_DIR/reporting/aws_logging/stats_updater.py -f ~/aws_logs/offline_recover/basic/aws-logfile-2011-0611-0000-full.basic.lc.stats -n 128
STOP_TIME=$(date +%s)
echo "0611:" $(((STOP_TIME-START_TIME)/60)) "minutes" >> ~/tmp/offline_basic_recover.log

START_TIME=$(date +%s)
python $APP_DIR/reporting/aws_logging/stats_updater.py -f ~/aws_logs/offline_recover/basic/aws-logfile-2011-0612-0000-full.basic.lc.stats -n 128
STOP_TIME=$(date +%s)
echo "0612:" $(((STOP_TIME-START_TIME)/60)) "minutes" >> ~/tmp/offline_basic_recover.log

START_TIME=$(date +%s)
python $APP_DIR/reporting/aws_logging/stats_updater.py -f ~/aws_logs/offline_recover/basic/aws-logfile-2011-0613-0000-full.basic.lc.stats -n 128
STOP_TIME=$(date +%s)
echo "0613:" $(((STOP_TIME-START_TIME)/60)) "minutes" >> ~/tmp/offline_basic_recover.log

START_TIME=$(date +%s)
python $APP_DIR/reporting/aws_logging/stats_updater.py -f ~/aws_logs/offline_recover/basic/aws-logfile-2011-0614-0000-full.basic.lc.stats -n 128
STOP_TIME=$(date +%s)
echo "0614:" $(((STOP_TIME-START_TIME)/60)) "minutes" >> ~/tmp/offline_basic_recover.log

START_TIME=$(date +%s)
python $APP_DIR/reporting/aws_logging/stats_updater.py -f ~/aws_logs/offline_recover/basic/aws-logfile-2011-0615-0000-full.basic.lc.stats -n 128
STOP_TIME=$(date +%s)
echo "0615:" $(((STOP_TIME-START_TIME)/60)) "minutes" >> ~/tmp/offline_basic_recover.log

START_TIME=$(date +%s)
python $APP_DIR/reporting/aws_logging/stats_updater.py -f ~/aws_logs/offline_recover/basic/aws-logfile-2011-0616-0000-full.basic.lc.stats -n 128
STOP_TIME=$(date +%s)
echo "0616:" $(((STOP_TIME-START_TIME)/60)) "minutes" >> ~/tmp/offline_basic_recover.log

START_TIME=$(date +%s)
python $APP_DIR/reporting/aws_logging/stats_updater.py -f ~/aws_logs/offline_recover/basic/aws-logfile-2011-0617-0000-full.basic.lc.stats -n 128
STOP_TIME=$(date +%s)
echo "0617:" $(((STOP_TIME-START_TIME)/60)) "minutes" >> ~/tmp/offline_basic_recover.log

START_TIME=$(date +%s)
python $APP_DIR/reporting/aws_logging/stats_updater.py -f ~/aws_logs/offline_recover/basic/aws-logfile-2011-0618-0000-full.basic.lc.stats -n 128
STOP_TIME=$(date +%s)
echo "0618:" $(((STOP_TIME-START_TIME)/60)) "minutes" >> ~/tmp/offline_basic_recover.log

START_TIME=$(date +%s)
python $APP_DIR/reporting/aws_logging/stats_updater.py -f ~/aws_logs/offline_recover/basic/aws-logfile-2011-0619-0000-full.basic.lc.stats -n 128
STOP_TIME=$(date +%s)
echo "0619:" $(((STOP_TIME-START_TIME)/60)) "minutes" >> ~/tmp/offline_basic_recover.log

START_TIME=$(date +%s)
python $APP_DIR/reporting/aws_logging/stats_updater.py -f ~/aws_logs/offline_recover/basic/aws-logfile-2011-0620-0000-full.basic.lc.stats -n 128
STOP_TIME=$(date +%s)
echo "0620:" $(((STOP_TIME-START_TIME)/60)) "minutes" >> ~/tmp/offline_basic_recover.log

START_TIME=$(date +%s)
python $APP_DIR/reporting/aws_logging/stats_updater.py -f ~/aws_logs/offline_recover/basic/aws-logfile-2011-0621-0000-full.basic.lc.stats -n 128
STOP_TIME=$(date +%s)
echo "0621:" $(((STOP_TIME-START_TIME)/60)) "minutes" >> ~/tmp/offline_basic_recover.log

START_TIME=$(date +%s)
python $APP_DIR/reporting/aws_logging/stats_updater.py -f ~/aws_logs/offline_recover/basic/aws-logfile-2011-0622-0000-full.basic.lc.stats -n 128
STOP_TIME=$(date +%s)
echo "0622:" $(((STOP_TIME-START_TIME)/60)) "minutes" >> ~/tmp/offline_basic_recover.log

START_TIME=$(date +%s)
python $APP_DIR/reporting/aws_logging/stats_updater.py -f ~/aws_logs/offline_recover/basic/aws-logfile-2011-0623-0000-full.basic.lc.stats -n 128
STOP_TIME=$(date +%s)
echo "0623:" $(((STOP_TIME-START_TIME)/60)) "minutes" >> ~/tmp/offline_basic_recover.log

START_TIME=$(date +%s)
python $APP_DIR/reporting/aws_logging/stats_updater.py -f ~/aws_logs/offline_recover/basic/aws-logfile-2011-0624-0000-full.basic.lc.stats -n 128
STOP_TIME=$(date +%s)
echo "0624:" $(((STOP_TIME-START_TIME)/60)) "minutes" >> ~/tmp/offline_basic_recover.log

START_TIME=$(date +%s)
python $APP_DIR/reporting/aws_logging/stats_updater.py -f ~/aws_logs/offline_recover/basic/aws-logfile-2011-0625-0000-full.basic.lc.stats -n 128
STOP_TIME=$(date +%s)
echo "0625:" $(((STOP_TIME-START_TIME)/60)) "minutes" >> ~/tmp/offline_basic_recover.log

START_TIME=$(date +%s)
python $APP_DIR/reporting/aws_logging/stats_updater.py -f ~/aws_logs/offline_recover/basic/aws-logfile-2011-0626-0000-full.basic.lc.stats -n 128
STOP_TIME=$(date +%s)
echo "0626:" $(((STOP_TIME-START_TIME)/60)) "minutes" >> ~/tmp/offline_basic_recover.log

START_TIME=$(date +%s)
python $APP_DIR/reporting/aws_logging/stats_updater.py -f ~/aws_logs/offline_recover/basic/aws-logfile-2011-0627-0000-full.basic.lc.stats -n 128
STOP_TIME=$(date +%s)
echo "0627:" $(((STOP_TIME-START_TIME)/60)) "minutes" >> ~/tmp/offline_basic_recover.log
