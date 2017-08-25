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
            ["Gen4S Single","FT_013_Install_SLES_IPv4_SingleNode_ADS","TC_20325_Ft_023_Upgrade_Single_Node_from_740_to_760","TC_20328_Ft_023_Upgrade_Single_Node_From_741_to_760","TC_20333_Ft_023_Upgrade_Single_Node_From_750_to_760"],
            ["Gen4S Multi","FT_014_Install_SLES_IPv4_MultiNode_ADS","FT_024_Upgrade_Multi_Node_from_740","FT_024_Upgrade_Multi_Node_from_741","FT_024_Upgrade_Multi_Node_from_750"]]
            #["Gen4T Single","None","None","None","None"],
            #["Gen4T Multi","FT_014_Install_SLES_IPv4_SingleNode_ADS_Gen4T","None","None","None"]]

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
            ["Gen4S Single","FT_013_Install_SLES_IPv4_SingleNode_ADS","TC_20325_Ft_023_Upgrade_Single_Node_from_740_to_760","TC_20328_Ft_023_Upgrade_Single_Node_From_741_to_760","TC_20333_Ft_023_Upgrade_Single_Node_From_750_to_760"],
            ["Gen4S Multi","FT_014_Install_SLES_IPv4_MultiNode_ADS","FT_024_Upgrade_Multi_Node_from_740","FT_024_Upgrade_Multi_Node_from_741","FT_024_Upgrade_Multi_Node_from_750"]]
            #["Gen4T Single","None","None","None","None"],
            #["Gen4T Multi","FT_014_Install_SLES_IPv4_SingleNode_ADS_Gen4T","None","None","None"]]

        self.css = """
                body {font-family: 'Open Sans', sans-serif;font-weight: 300;line-height: 1.42em;color:#A7A1AE;background-color:#1F2739;}
                .title h2 {font: normal 20px/100%;font-size:3em;font-weight: 300;line-height:1em;text-align: center;margin-top:50px;}
                .datagrid table {border-collapse: collapse; text-align: center;width: 80%;margin-left:150px; border:none;}
                .datagrid table td,
                .datagrid table tr { padding: 20px 80px; }
                .datagrid table thead th {padding:10px 80px;background-color: #1F2739;font-size: 15px;text-align:center;}
                .datagrid table tbody tr td {color: #4DC3FA; border:2px solid #A2B5CD;font-size: 16px;font-weight: bold;}

                .datagrid table tbody .odd td { background: #323C50; border: 2px solid #1F2739; }
                .datagrid table tbody .even td { background: #2C3446; border: 2px solid #1F2739; }
                .blue { color: #4DC3FA; }
                .yellow { color: #FFF842; }
                .orange { color: #FB667A;}
                .green { color: #32CD32;}
              """
        self.tableTitle = ["Platform","Fresh Install 7.6.0","Upgrade From 7.5.0","Upgrade From 7.4.1","Upgrade From 7.4.0"]
        self.testResult = testResultRaw
        self.reportFolder = reportFolder
        self.urlHead = "http://vmdur-wfq-193-70.asl.lab.emc.com:8080/job/"
        #self.urlTail = "/lastBuild/robot/report/log.html"
    def getBuildVersion(self,folder):
        versionFile = [folder+x for x in os.listdir(folder) if "xml" in x][0]
        #print "versionFile : ",versionFile
        pattern = re.compile("7\.6\.0\.[0-9]{1,3}")
        versionFromFile = re.findall(pattern,open(versionFile,'r').read())[0]
        versionFromFolder = re.findall(pattern,folder)[0]
        return (cmp(versionFromFile,versionFromFolder) and versionFromFolder or versionFromFile)
    def genHtml(self):
        h = HTML('html')
        h.title('Test Report')
        h.text('<style>{}</style>'.format(self.css),escape=False)
        bodyTitle = h.body()
        titleDiv = bodyTitle.div(klass = "title")
        currentBuildVersion = self.getBuildVersion(self.reportFolder)
        #h2 = titleDiv.h2("Workflow Install & Upgrade Matrix - "+ currentBuildVersion)
        h2 = titleDiv.h2()
        h2.span("Workflow Install & Upgrade Matrix - ",klass = "blue")
        h2.span(currentBuildVersion,klass = "yellow")

        datagrid = bodyTitle.div(klass = "datagrid")
        table = datagrid.table(klass = "container")
        tableHead = table.thead()
        for t in self.tableTitle:
            tableHead.th("%s"%t)
        flag = 0
        tbody = table.tbody()
        for item in self.TABLE_STRUCTURE:
            if 0 != flag % 2:
                tr = tbody.tr(klass = "odd")
            else : 
                tr = tbody.tr(klass = "even")
            flag += 1
            tr.td("%s"%item[0])
            for i in range(1,len(item)):
                if self.testResult.has_key(item[i]):
                    #td = tr.td("%s"%self.testResult[item[i]][0])
                    td = tr.td()
                    tagA = td.a(href = self.urlHead+self.testResult[item[i]][1],target = "__blank")
                    if self.testResult[item[i]][0] == rFAIL:
                        font = tagA.font(self.testResult[item[i]][0],color = "#FB667A")
                        #tagA.span(self.testResult[item[i]][0],klass = "orange")
                        
                    elif self.testResult[item[i]][0] == rPASS :
                        #tagA.span(self.testResult[item[i]][0],klass = "green")
                        font = tagA.font(self.testResult[item[i]][0],color = "green")
                else :
                    td = tr.td("N/A")
                td.nbsp()
                td.nbsp()
            
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
        msg['SUBJECT'] = "Workflow Install & Upgrade Report"
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
    with open("/mnt/wf_qa_ci/builds/sanity/lastBuild.txt",'r') as fp:
        version = fp.read()
    folder = "/mnt/wf_qa_ci/builds/sanity/"+version.strip()+os.sep
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
    mailList = ["fugui.xu@emc.com","kyle.jia@emc.com","elsa.chen@emc.com","Gerald.Mei@emc.com","Stephen.Shao@emc.com","Arthur.Zhou@emc.com","Harrison.Feng@emc.com"]
    mail = SendEmail(htmlContent)
    #for name in mailList:
    #    mail.email_report("ci_report@emc.com",name)
    mail.email_report("ci_report@emc.com",mailList[0])
    print "sending mail..."
