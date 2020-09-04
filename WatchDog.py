# -*- coding: utf-8 -*-
# Author: MySour
# Date: 2020-9-1
# Version: 0.9

import requests
from bs4 import BeautifulSoup
import re
import sys


class Crawler():
    def __init__(self, file):
        self.s = requests.session()
        self.file = file
        self.page_size = 500
        self.url = 'http://apps.webofknowledge.com/OutboundService.do'
        self.querystring = {"action": "go", "": ""}
        self.user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.83 Safari/537.36'

    # 发送POST请求获取单批次的论文信息，一批500篇
    def post_to_single_page(self, sid, qid, markFrom, markTo):
        payload = "selectedIds=&displayCitedRefs=true&displayTimesCited=true&displayUsageInfo=true&viewType=summary&product=WOS&mark_id=WOS&colName=WOS&search_mode=AdvancedSearch&locale=zh_CN&view_name=WOS-summary&sortBy=PY.D%3BLD.D%3BSO.A%3BVL.D%3BPG.A%3BAU.A&mode=OpenOutputService&qid=" + qid + "&SID=" + sid + "&format=saveToFile&filters=PMID%20AUTHORSIDENTIFIERS%20ACCESSION_NUM%20ISSN%20CONFERENCE_SPONSORS%20ABSTRACT%20CONFERENCE_INFO%20SOURCE%20TITLE%20AUTHORS&mark_to=" + str(
            markTo) + "&mark_from=" + str(
            markFrom) + "&count_new_items_marked=0&use_two_ets=false&IncitesEntitled=yes&value(record_select_type)=range&fields_selection=PMID%20AUTHORSIDENTIFIERS%20ACCESSION_NUM%20ISSN%20CONFERENCE_SPONSORS%20ABSTRACT%20CONFERENCE_INFO%20SOURCE%20TITLE%20AUTHORS&save_options=fieldtagged"
        headers = {
            'content-type': "application/x-www-form-urlencoded",
            'origin': "http://apps.webofknowledge.com",
            'referer': "http://apps.webofknowledge.com/summary.do?product=WOS&doc=1&qid=%s&SID=%s&search_mode=AdvancedSearch&update_back2search_link_param=yes" % (
                qid, sid),
            'user-agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.135 Safari/537.36"
        }

        response = requests.request("POST", self.url, data=payload, headers=headers, params=self.querystring)
        return response.text

    # 追加写入文件中
    def write_to_file_append(self, content):
        with open(file=self.file, mode='a', encoding='utf-8') as file_object:
            file_object.write(content)
            file_object.write('\n')

    # 下载导出的论文信息文件
    def download(self, sid, qid, total):
        mark_from = 1
        mark_to = 1
        while (True):
            if mark_from + 499 > total:
                mark_to = total
            else:
                mark_to = mark_from + 499

            if (mark_to > total or mark_from > total):
                break
            print('Ready to send post request to get content. Record Range: %d to %d' % (mark_from, mark_to))
            content = self.post_to_single_page(sid, qid, mark_from, mark_to)
            print('Get record success! Size: %d' % len(content))
            self.write_to_file_append(content)
            mark_from = mark_to + 1

    # 访问搜索主页，获取所有搜索式信息
    def visit(self, url):
        homepage_request = requests.get(url)
        soup = BeautifulSoup(homepage_request.text, 'lxml')
        trs = soup.findAll('table')[20].findAll('tr', id=re.compile('.*_row'))
        result = {}
        print('查询到如下搜索式，格式[序号](命中个数) 搜索表达式：')
        for tr in trs:
            hitCount = int(tr.find('a', id='hitCount').get_text().replace(',', ''))
            query = tr.find('div', class_='historyQuery').get_text()
            qid = re.findall(r'qid=\d+&', tr.find('a', id='hitCount')['href'])[0].replace('qid=', '').replace('&', '')
            result[int(qid)] = hitCount
            print('[%s](%d) %s' % (qid, hitCount, query))
        choose = int(input('请输入中括号的数字进行选择>'))
        return [str(choose), result[choose]]


if __name__ == '__main__':
    # 浏览器中的地址
    homepage_url = "http://apps.webofknowledge.com/WOS_AdvancedSearch_input.do?product=WOS&search_mode=AdvancedSearch&replaceSetId=&goToPageLoc=SearchHistoryTableBanner&SID=7DAYTtvIPR95hbhaHGh&errorQid=12#SearchHistoryTableBanner"
    # 想要输出的文件名
    file_name = "output.txt"

    if len(homepage_url) == 0 or len(file_name) == 0:
        print("Please add url&output file name! ")
        sys.exit(-1)

    sid = re.findall(r'SID=\w+&', homepage_url)[0].replace('SID=', '').replace('&', '')
    crawler = Crawler(file=file_name)
    result = crawler.visit(homepage_url)
    qid = result[0]
    hitCount = result[1]
    print('现在开始爬取所有命中论文的信息,总计：%d' % hitCount)
    crawler.download(sid, qid, hitCount)
    print('爬取结束！')
