from requests_html import HTMLSession
import datetime


def find(text, element):
    try:
        index = text.index(element)
        return text[index+1]
    except:
        return ''


def scrape(irnis):
    session = HTMLSession()
    headers = {
        "User-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.163 Safari/537.36 OPR/67.0.3575.137"}
    data = {}
    status_url = f'https://tsdr.uspto.gov/statusview/sn{irnis}'
    docs_url = f'https://tsdr.uspto.gov/docsview/sn{irnis}'
    # FETCHING STATUS RELEATED DETAILS
    html = session.get(status_url)
    html = html.html
    text = html.text.split('\n')
    # Finding Mark
    summarySection = html.find('div#sumary-section')

    # Finding Mark
    data['Mark'] = ''
    mark = summarySection[0].find('div.value.markText')
    if len(mark) > 0:
        data['Mark'] = mark[0].text
    else:
        data['Mark'] = ''
    # Finding Us Serial Number
    us_serial_number = summarySection[0].find('div.double.table')
    data['US Serial Number'] = ''
    data['Application Filing Date'] = ''
    if len(us_serial_number) > 0:
        element = us_serial_number[0].find('div.value')
        if len(element) > 0:
            data['US Serial Number'] = element[0].text
            data['Application Filing Date'] = element[1].text
        else:
            data['US Serial Number'] = ''
            data['Application Filing Date'] = ''
    # Finding Mark Type:
    mark_type = summarySection[0].find('div.row')
    data['Mark Type'] = ''
    for i in range(len(mark_type)):
        temp = mark_type[i].text.strip('\n')

        if temp.find('Mark Type:') != -1:
            temp = temp.split('\n')
            if len(temp) > 1:
                data['Mark Type'] = temp[1]
                break
    # Finding TM5
    data['TM5 Common Status Descriptor'] = ''
    Tm5 = summarySection[0].find('div.double.table')
    for i in Tm5:
        temp = i.text
        if temp.find('TM5 Common Status Descriptor') != -1:
            data['TM5 Common Status Descriptor'] = '\n'.join(
                i.text.split('\n')[1:])
            break

    # Finding Status Date :
    status_date = summarySection[0].find('div.row')
    data['Status Date'] = ''
    data['Publication Date'] = ''
    data['Date Abandoned'] = ''
    for i in range(len(status_date)):
        temp = status_date[i].text.strip('\n')
        if temp.find('Date') != -1 and temp.find('Application Filing Date:') == -1:
            temp = temp.split('\n')
            if len(temp) > 1:
                data[temp[0].replace(':', '')] = temp[1]

    # Mark Information Done:

    # Finding Goods and Service Details
    data['International Class(es)'] = ''
    try:
        temp = text.copy()
        temp.reverse()
        # Getting Last Occurance
        index = temp.index('International Class(es):')
        data['International Class(es)'] = temp[index-1]
    except:
        data['International Class(es)'] = ''
    # Owner Information
    ownerInfo = html.find('div#relatedProp-section')
    data['Owner Name'] = ''
    data['Legal Entity Type'] = ''
    data['Owner Address'] = ''
    if len(ownerInfo) > 0:
        elements = ownerInfo[0].find('div.single.table')
        for i in elements:
            temp = i.text
            if temp.find('Owner Name:') != -1:
                data['Owner Name'] = ' '.join(temp.split('\n')[1:])
                continue
            if temp.find('Owner Address:') != -1:
                data['Owner Address'] = '\n'.join(temp.split('\n')[1:])

        elements = ownerInfo[0].find('div.double.table')
        for i in elements:
            temp = i.text
            if temp.find('Legal Entity Type:') != -1:
                data['Legal Entity Type'] = temp.split('\n')[1]
                break
    # Finding Email and Phone Number:
    sections = html.find('div.expand_wrapper.default_hide')
    index = -1
    for i in range(len(sections)):
        if sections[i].text.find('Attorney/Correspondence Information') != -1:
            index = i
            break
    if index != -1:
        correspondence = sections[index]
        data['Correspondent Name/Address'] = ''
        data['Phone No'] = ''
        data['Email'] = ''
        info = correspondence.find('div.single.table')
        for i in info:
            temp = i.text
            if temp.find('Correspondent Name/Address:') != -1:
                data['Correspondent Name/Address'] = '\n'.join(
                    temp.split('\n')[1:])
                break
        info = correspondence.find('div.double.table')
        for i in info:
            temp = i.text
            if temp.find('Phone:') != -1 and ("Representative") not in temp:
                data['Phone No'] = ''.join(temp.split('\n')[1])
            if temp.find('Correspondent e-mail:') != -1:
                data['Email'] = ''.join(temp.split('\n')[1])
                break
                

    # END OF FETCHING STATUS RELATED DETAILS:

    # FETCHING DOCUMENTS RELATED DETAILS
    html = session.get(docs_url, headers=headers)
    html = html.html
    data['Document Date'] = ''
    data['Document Title'] = ''
    data['Office  Action Date '] = ''
    tbody = html.find('tbody#docResultsTbody')
    if len(tbody) > 0:
        trs = tbody[0].find('tr.doc_row.dataRowTR')
        docs = []
        for i in trs:
            temp = i.text.split('\n')
            docs.append(temp)
        for i in docs:
            temp = i[0].split(' ')
            month = temp[0][:3]
            day = temp[1][:2]
            year = temp[2][:4]
            i[0] = f'{month} {day} {year}'

        docs.sort(key=lambda x: [datetime.datetime.strptime(
            x[0], '%b  %d %Y'), int(x[-1])])
        data['Document Date'] = docs[-1][0]
        data['Document Title'] = docs[-1][1]

    # Targeting xPath
    # tbody = html.find('tbody#docResultsTbody')
    # td = tbody[0].xpath('//*[@id="docResultsTbody"]/tr[1]/td[3]')
    # print(td[0].text)

    # # Finding First Off Action Outgoing

    sections = html.find('tr.doc_row.dataRowTR')
    docs = []
    j = 0
    prev = []
    text = '\n'.join([i.text for i in sections]).split('\n')
    for i in range(len(text)):
        if text[i].find('Offc Action Outgoing') != -1:
            if j == 0:
                j += 1
                prev = [text[i-1], text[i], text[i+2]]
            docs.append([text[i-1], text[i], text[i+2]])

    sameDocs = [i for i in docs if i[0] == prev[0]]
    docId = -1

    if len(sameDocs) > 0:
        data['Office  Action Date '] = sameDocs[-1][0]
        docId = sameDocs[-1][-1]
    data['SUMMARY OF ISSUES'] = ''

    # print(documents)

    if docId != -1:
        url = f'https://tsdrsec.uspto.gov/ts/cd/casedoc/sn{irnis}/OOA{docId}/1/webcontent?scale=1'
        html = session.get(url, headers=headers)
        html = html.html
        # Finding Summary of Issues:
        elements = html.find('p.MsoNormal')
        t = ''
        for i in range(len(elements)):
            temp = elements[i].text.upper()
            if temp.find('SUMMARY OF ISSUES') != -1:
                p = html.find('p')
                flag = False
                for j in range(i+1, int(len(p)/1.5)):
                    try:
                        tmp = p[j].attrs['class'][0].upper()
                        if tmp.find('MSOLISTPARAGRAPHCXSP') != -1:
                            t += p[j].text + '\n'
                            flag = True
                    except:
                        continue
                if flag:
                    break
                ol = html.find('ol', first=True)
                ul = html.find('ul', first=True)

                if ol is not None:
                    t = ol.text
                elif ul is not None:
                    t = ul.text
                break
        data['SUMMARY OF ISSUES'] = '\n'.join(t.split('\n'))

    return data


if __name__ == '__main__':
    print(scrape('79319876'))
# 76709358
