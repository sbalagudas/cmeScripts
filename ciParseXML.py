#!/usr/bin/python
import os
import sys
import re
import xml.etree.cElementTree as ET
from html import HTML

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

rPASS = u"PASS"
rFAIL = u"FAIL"

##############################################
## parse output.xml and get test result
##############################################
class GetReportResult(object):
    def __init__(self):
        self.results = dict()
        #self.results = list()
        self.TABLE_STRUCTURE=[
            ["VMWare","FT_011_Daily_Install_AVE","FT_026_Upgrade_Server_Only_from_740","FT_026_Upgrade_Server_Only_from_741","FT_026_Upgrade_Server_Only_from_750"],
            ["Hyper-V","None","FT_022_Upgrade_AVE_HyperV_from_740","FT_022_Upgrade_AVE_HyperV_from_741","FT_022_Upgrade_AVE_HyperV_from_750"],
            ["GenS Single","FT_013_Install_SLES_IPv4_SingleNode_ADS","TC_20325_Ft_023_Upgrade_Single_Node_from_740_to_760","TC_20328_Ft_023_Upgrade_Single_Node_From_741_to_760","TC_20333_Ft_023_Upgrade_Single_Node_From_750_to_760"],
            ["GenS Multi","FT_014_Install_SLES_IPv4_MultiNode_ADS","FT_024_Upgrade_Multi_Node_from_740","FT_024_Upgrade_Multi_Node_from_741","FT_024_Upgrade_Multi_Node_from_750"],
            ["Gen4T Single","None","None","None","None"],
            ["Gen4T Multi","FT_014_Install_SLES_IPv4_SingleNode_ADS_Gen4T","None","None","None"]]

    def getCaseNameAndStatus(self,node,fileName):
        tmpNode = node.findall("suite")
        if 0 <  len(tmpNode) :
            for nd in tmpNode :
                self.getCaseNameAndStatus(nd,fileName)
        else :
            [self.results.update(x) for x in [{x.attrib['name'] : [x.find('status').attrib['status'],fileName.split("/")[-1][:-4]]} for x in node.findall('test')]]

    def parseOneXML(self,fileName):
        tree = ET.parse(fileName)
        root = tree.getroot()
        childOfRoot = root.getchildren()
        caseDict = dict()
    
        self.getCaseNameAndStatus(root,fileName)
    
    def parseFolderXml(self,folder):    
        if os.path.exists(folder) and os.path.isdir(folder):
            files = [folder+x for x in os.listdir(folder) if os.path.isfile(folder+x) and x.endswith('xml')]
            for eachFile in files:
                #print "----reading file : %s"%(eachFile)
                self.parseOneXML(eachFile)
        return self.results
 
    def formateResult(self,data):
        if 0 == len(data):
            print "no test results."
            sys.exit()
        newData = list()
        for item in self.TABLE_STRUCTURE:
            tmpList = list()
            tmpList.append(item[0])
            for i in range(1,len(item)): #item[i] in ['None','None','None','None']
                try :
                    if data.has_key(item[i]):
                        tmpList.append(data[item[i]])
                    else : 
                        tmpList.append("N/A")
                except KeyError:
                    pass
            newData.append(tmpList)
        return  newData

##############################################
## generating html content with the test results
##############################################
class GenHTML(object):
    def __init__(self,testResultRaw,reportFolder):
        self.TABLE_STRUCTURE=[
            ["VMWare","FT_011_Daily_Install_AVE","FT_026_Upgrade_Server_Only_from_740","FT_026_Upgrade_Server_Only_from_741","FT_026_Upgrade_Server_Only_from_750"],
            ["Hyper-V","None","FT_022_Upgrade_AVE_HyperV_from_740","FT_022_Upgrade_AVE_HyperV_from_741","FT_022_Upgrade_AVE_HyperV_from_750"],
            ["GenS Single","FT_013_Install_SLES_IPv4_SingleNode_ADS","TC_20325_Ft_023_Upgrade_Single_Node_from_740_to_760","TC_20328_Ft_023_Upgrade_Single_Node_From_741_to_760","TC_20333_Ft_023_Upgrade_Single_Node_From_750_to_760"],
            ["GenS Multi","FT_014_Install_SLES_IPv4_MultiNode_ADS","FT_024_Upgrade_Multi_Node_from_740","FT_024_Upgrade_Multi_Node_from_741","FT_024_Upgrade_Multi_Node_from_750"],
            ["Gen4T Single","None","None","None","None"],
            ["Gen4T Multi","FT_014_Install_SLES_IPv4_SingleNode_ADS_Gen4T","None","None","None"]]

        self.css = """
                .title h2 {color:#1C86EE; font : normal 40px/100% Arial, Helvetica, sans-serif;font-weight: bold;text-align:center;background-image:url("img/blue5.jpg");margin-left:30px;margin-right:50px;}
                .datagrid table {  border-collapse: collapse; text-align: center; width: 95%;margin-left:30px; bgcolor:#00557F;border:3px solid #E1EEF4}
                .datagrid {font: normal 20px/150% Arial, Helvetica, sans-serif; background: #fffff;  -webkit-border-radius: 3px; -moz-border-radius: 3px; border-radius: 3px; }
                .datagrid table td,
                .datagrid table tr { padding: 20px 80px; }
                .datagrid table thead {background:-webkit-gradient( linear, center top, left bottom, color-stop(0.05, #006699), color-stop(1, #00557F) );background:-moz-linear-gradient( center top, #006699 5%, #00557F 100% );filter:progid:DXImageTransform.Microsoft.gradient(startColorstr='#006699', endColorstr='#00557F');background-color:#006699; color:#FFFFFF; font-size: 25px; font-weight: bold; border-left: 1px solid #0070A8; }
                .datagrid table thead :first-child { border: none; }
                .datagrid table tbody tr td { color: #4876FF; border:2px solid #E1EEF4;font-size: 16px;font-weight: bold; bgcolor: #F4A460}
                .datagrid table tbody .alt td { background: #98F5FF; color: #00557F;border: 2px solid #E1EEf4; }
                .datagrid table tbody td:first-child { border-left: none;font : bold 25px/100% Arial, Helvetica, sans-serif ;bgcolor:}
                .datagrid table tbody tr:last-child td { border-bottom: solid; }
              """
        self.tableTitle = ["Platform","Fresh Install 7.6.0ss","Upgrade From 7.5.0","Upgrade From 7.4.1","Upgrade From 7.4.0"]
        self.testResult = testResultRaw
        self.reportFolder = reportFolder
        self.urlHead = "http://vmdur-wfq-193-70.asl.lab.emc.com:8080/job/"
        self.urlTail = "/lastBuild/robot/report/log.html"
    def getBuildVersion(self,folder):
        versionFile = [folder+os.sep+x for x in os.listdir(folder) if "xml" in x][0]
        #print "versionFile : ",versionFile
        pattern = re.compile("7.6.0.[0-9]{1,3}")
        return re.findall(pattern,open(versionFile,'r').read())[0]
    def genHtml(self):
        h = HTML('html')
        h.title('Test Report')
        h.text('<style>{}</style>'.format(self.css),escape=False)
        bodyTitle = h.body()
        titleDiv = bodyTitle.div(klass = "title")
        currentBuildVersion = self.getBuildVersion(self.reportFolder)
        h2 = titleDiv.h2("Avamar Workflow CI Report For "+ currentBuildVersion)

        datagrid = bodyTitle.div(klass = "datagrid")
        table = datagrid.table()
        tableHead = table.thead()
        for t in self.tableTitle:
            tableHead.th("%s"%t)
        flag = 0
        tbody = table.tbody()
        for item in self.TABLE_STRUCTURE:
            if 0 != flag % 2:
                tr = tbody.tr(klass = "alt")
            else : 
                tr = tbody.tr()
            flag += 1
            tr.td("%s"%item[0])
            for i in range(1,len(item)):
                if self.testResult.has_key(item[i]):
                    #td = tr.td("%s"%self.testResult[item[i]][0])
                    td = tr.td()
                    if self.testResult[item[i]][0] == rFAIL:
                        tagA = td.a(href = self.urlHead+self.testResult[item[i]][1]+self.urlTail,target = "__blank")
                        font = tagA.font(self.testResult[item[i]][0],color = "red")
                    elif self.testResult[item[i]][0] == rPASS :
                        tagA = td.a(href = self.urlHead+self.testResult[item[i]][1]+self.urlTail,target = "__blank")
                        font = tagA.font(self.testResult[item[i]][0],color = "green")
                else :
                    td = tr.td("N/A")
            
        return h 

    def writeHtmlToFile(self,targetFile,htmlContent):
        with open(targetFile,'w') as f :
            for content in htmlContent:
                f.write(content)
            f.close()

###############################
## sending the email  
###############################
class SendEmail(object):
    def __init__(self,htmlContent):
        self.html = htmlContent
        #print "======self.html",self.html
    def email_report(self,sender, recepients):
        SERVER = "localhost"
        msg = MIMEMultipart('alternative')
        msg['FROM'] = sender
        msg['BCC'] = ", ".join(recepients)
        msg['SUBJECT'] = "testing"
        part2 = MIMEText(self.html, 'html')

        # Attach parts into message container.
        # According to RFC 2046, the last part of a multipart message, in this case
        # the HTML message, is best and preferred.
        #msg.attach(part1)
        msg.attach(part2)

        # Send the mail

        server = smtplib.SMTP(SERVER)
        server.sendmail(sender, recepients, msg.as_string())
        server.quit()

    
if __name__ == "__main__":
    ###############################
    ## get test raw data  
    ###############################
    print "geting test raw data..."
    folder = "/mnt/wf_qa_ci/builds/sanity/7.6.0.53/"
    getResultIns = GetReportResult()
    testResult = getResultIns.parseFolderXml(folder)
    ###############################
    ## generating html
    ###############################
    print "generating html..."
    tmpHtmlFile = os.getcwd()+os.sep+"tmpHtml.html" 
    H = GenHTML(testResult,folder)
    html = H.genHtml()
    H.writeHtmlToFile(tmpHtmlFile,html)
    with open(tmpHtmlFile,'r') as f:
        htmlContent = f.read()
    ###############################
    ## sending email
    ###############################
    mailList = ["fugui.xu@emc.com","kyle.jia@emc.com","elsa.chen@emc.com"]
    mail = SendEmail(htmlContent)
    #mail = SendEmail(htmlContent)
    mail.email_report("fugui.xu@emc.com",mailList[2])
    print "sending mail..."
