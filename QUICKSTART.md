
================================================================================
🚀 QUICK START - 立即开始人才检索
================================================================================

【步骤1】打开搜索链接
$ cd /Users/cooga/.openclaw/workspace/Project/TalentIntel
$ open data/xray_campaigns/extended_links_20260304_101931.html

【步骤2】安装浏览器插件
Chrome:  Linkclump
Firefox: Multi-Link Paste

【步骤3】执行搜索并提取链接
1. 在浏览器中点击第一个策略的搜索链接
2. 框选搜索结果中的所有LinkedIn链接
3. 复制并保存到 links.txt 文件
4. 重复上述步骤处理多个策略

【步骤4】批量评估
$ python3 scripts/batch_evaluate.py links.txt

【步骤5】查看进度
$ python3 scripts/aggregate_talent_data.py

================================================================================
