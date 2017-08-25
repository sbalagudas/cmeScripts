#!/usr/bin/bash

SANITY_PATH="/mnt/wf_qa_ci/builds/sanity"
LAST_VERSION="/mnt/wf_qa_ci/builds/sanity/lastBuild.txt"
FILE_LIST=(Daily_Install_Rooster_AVE.xml View_7.6.0_Install_SingleNode_Gen4S.xml View_7.6.0_Upgrade_MultiNode_Gen4S.xml View_7.6.0_Upgrade_VMWare_AVE.xml View_7.6.0_Install_MultiNode_Gen4S.xml  View_7.6.0_Upgrade_HyperV_AVE.xml View_7.6.0_Upgrade_SingleNode_Gen4S.xml)


function getLatestVersion()
{
    #echo "getting the latest folder..."
    latest=`ls ${SANITY_PATH}| grep -P -o "\d.\d.\d.\d+"| sort -n | tail -1`
    echo "latest build version : ${latest}"
}

function compareVersion()
{
    latestSubVersion=`echo $1 | cut -d '.' -f 4`
    lastBuildSubVersion=`echo $2 | cut -d'.' -f 4`
    #echo "latest : $1 : ${latestSubVersion}"
    #echo "last : $2 : ${lastBuildSubVersion}"
    fileCnt=`ls ${SANITY_PATH}/$1|grep xml | wc -l`
    if [ ${latestSubVersion} -gt ${lastBuildSubVersion} ];then 
        #if [ ${fileCnt} -eq 7 ];then
        echo $1 > ${LAST_VERSION} 
        /usr/bin/python ${SANITY_PATH}/bin/reportHandler.py
        #elif [ ${fileCnt} -lt 7 ];then
        for file in ${FILE_LIST[*]}
        do 
            cnt=`ls ${SANITY_PATH}/$1 | grep ${file} | wc -l`
            #echo "command : ls ${SANITY_PATH}/$1 | grep ${file} | wc -l"
            #echo "cnt : ${cnt}"
            if [ ${cnt} -eq 0 ];then
                echo "missing file : ${file}"
            fi
        done
        #fi
    else
        echo "no newer build come..."
        echo "-----------------------------"
        echo "| last build | latest build |"
        echo "|   $2 |   $1   |"
        echo "-----------------------------"

    fi
}

function checkIfMailNeeded()
{
    if [ -f ${LAST_VERSION} ];then
        lastBuild=`cat ${LAST_VERSION}`
        if [ X${lastBuild} != X ];then
            compareVersion ${latest} ${lastBuild}
        else 
#            /usr/bin/python ${SANITY_PATH}/ciReport.py
            echo ${latest} > ${LAST_VERSION}
        fi
    else 
        echo "file : ${LAST_VERSION} does not exist, creating..."
        echo ${latest} > ${LAST_VERSION}
        /usr/bin/bash ${SANITY_PATH}/ciReport.sh
    fi
}

function main()
{
  getLatestVersion
  checkIfMailNeeded
}

main
