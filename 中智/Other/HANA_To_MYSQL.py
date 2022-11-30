# -*- coding: utf-8 -*-
'''
@createTool    : PyCharm-2020.2.2
@projectName   : pythonProject
@originalAuthor: Made in win10.Sys design by deHao.Zou
@createTime    : 2020/10/21 10:10
'''
import pandas as pd
import numpy as np
import pyhdb  # 加载连接HANA的所需模块
import re
from xlrd import xldate_as_tuple
import openpyxl
import glob
import time
import datetime
from termcolor import cprint
from time import strftime, gmtime
from sqlalchemy import create_engine  # 连接mysql模块
from sqlalchemy.types import Integer, NVARCHAR, Float

"""
=======================================================================
HANA信息详情                                                           #
=======================================================================
HANA地址：192.168.20.183                                               #
HANA端口：30015                                                        #
HANA名：Hana106620                                                     #
HANA密码：CHENjia90                                                    #
拜访表名：HBP(HANA106620).Content.HD-HAND.SD.POWER_BI.CV_ZHRWQBF11      #
离店表名：HBP(HANA106620).Content.HD-HAND.SD.POWER_BI.CV_ZHRWQBF12      #
------------------------------------------------------------------------
------------------------------------------------------------------------
------------------------------------------------------------------------
========================================================================
MySQL信息详情                                                           #
========================================================================
MySQL地址：192.168.20228                                                #
MySQL端口：3306                                                         #
MySQL名(一般默认): root                                                  #
MySQL密码：123456                                                       #
数据上传位置：alex -> sfa -> sfa_bf_fact                                  #
------------------------------------------------------------------------
需求：
从HANA里面提取拜访表与签退表两张表数据，合并两张表（匹配拜访时间与签退时间），把处理好的表上传数据库保存。
"""

allStartTime = datetime.datetime.now()


def dataHANA():
    print("HANA数据获取ing......")
    try:
        hanaStartTime = datetime.datetime.now()

        # 获取 Connection 对象
        def get_HANA_Connection():
            connection_Obj = pyhdb.connect(
                host="192.168.20.183",  # HANA地址
                port=30015,  # HANA端口号
                user="Hana106620",  # 用户名
                password="CHENjia90"  # 密码
            )
            return connection_Obj

        def get_matBF(conn):
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM "HD-HAND.SD.POWER_BI::CV_ZHRWQBF11"')  # 连接拜访表
            mat = cursor.fetchall()
            return mat

        def get_matQT(conn):
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM "HD-HAND.SD.POWER_BI::CV_ZHRWQBF12"')  # 连接签退表
            mat = cursor.fetchall()
            return mat

        conn = get_HANA_Connection()
        dataBF = pd.DataFrame(get_matBF(conn))
        dataQT = pd.DataFrame(get_matQT(conn))
        # dataBF.to_excel("D:/DataCenter/BFQT/mergeTable_BF_QT/BF-QT/dataBF.xlsx", index=False)
        # dataQT.to_excel("D:/DataCenter/BFQT/mergeTable_BF_QT/BF-QT/dataQT.xlsx", index=False)
        hanaEndTime = datetime.datetime.now()
        print("HANA数据获取成功！！！")
        print("拜访表数据有" + str(len(dataBF)) + "行")
        print("签退表数据有" + str(len(dataQT)) + "行")
        print("<HANA数据获取end>耗时：" + str((hanaEndTime - hanaStartTime).seconds) + "秒")

        mtStartTime = datetime.datetime.now()
        print("开始合并拜访签退表ing......")
        # bf = pd.read_excel('D:/DataCenter/BFQT/mergeTable_BF_QT/BF-QT/dataBF.xlsx', sheet_name=0, header=0, index_col=None)
        # qt = pd.read_excel('D:/DataCenter/BFQT/mergeTable_BF_QT/BF-QT/dataQT.xlsx', sheet_name=0, header=0, index_col=None)
        dataBF.columns = ['MANDT_QD', 'OBJECTI_QD', 'NAME_QD', 'STAFF_DESC_QD', 'SY_DEPT_DESC_QD', 'SY_SFA_DESC_QD',
                          'SY_POINT_DESC_QD', 'F0000003_QD', 'SY_SFA_BINARYCODE_QD', 'SY_TYPE_QD', 'SY_SFA_ID_QD',
                          'SY_BFDATE_QD', 'key_QD', 'CREATEDBY_QD', 'SY_BFTIME_QD', 'MODIFIEDBY_QD', 'MODIFIEDTIME_QD',
                          'CREATEDBYOBJECT_QD', 'OWNERIDOBJECT_QD', 'OWNERDEPTIDOBJECT_QD', 'MODIFIEDBYOBJECT_QD',
                          'SY_LATITUDE_QD', 'SY_LONGITUDE_QD', 'STAFF_ID_QD', 'SY_DEPT_ID_QD']

        dataQT.columns = ['MANDT_QT', 'OBJECTID_QT', 'NAME_QT', 'STAFF_DESC_SECOND_QT', 'SY_DEPT_DESC_QT',
                          'SY_POINT_DESC_QT', 'SY_PHOTO_QT', 'SY_SFA_BINARYCODE_QT', 'SY_SFA_DESC_QT', 'SY_QTDATE_QT',
                          'XIAOJIE_QT', 'STAFF_DESC_FIRST_QT', 'SY_QTTIME_QT', 'MODIFIEDBY_QT', 'MODIFIEDTIME_QT',
                          'CREATEDBYOBJECT_QT', 'OWNERIDOBJECT_QT', 'OWNERDEPTIDOBJECT_QT', 'MODIFIEDBYOBJECT_QT',
                          'SY_LATITUDE_QT', 'SY_LONGITUDE_QT', 'STAFF_ID_QT', 'SY_DEPT_ID_QT', 'SY_SFA_ID_QT']

        dataBF['SY_BFTIME_QD'] = pd.to_datetime(dataBF['SY_BFTIME_QD'])
        dataQT['SY_QTTIME_QT'] = pd.to_datetime(dataQT['SY_QTTIME_QT'])

        '''
        数据预处理（清洗掉拜访时间、签退时间、人员编号和门店编号异常的数据）
        '''
        for i in range(len(dataBF['STAFF_ID_QD'])):
            if dataBF.loc[i, 'STAFF_ID_QD'] == 0:
                dataBF.loc[i, 'STAFF_ID_QD'] = "NA"
        dataBF = dataBF[~dataBF['STAFF_ID_QD'].isin(['NA'])]

        for j in range(len(dataQT['STAFF_ID_QT'])):
            if dataQT.loc[j, 'STAFF_ID_QT'] == 0:
                dataQT.loc[j, 'STAFF_ID_QT'] = "NA"
        dataQT = dataQT[~dataQT['STAFF_ID_QT'].isin(['NA'])]

        dataBF_notNull = ['SY_SFA_ID_QD', 'STAFF_ID_QD', 'SY_BFTIME_QD', 'SY_TYPE_QD']
        for k in dataBF_notNull:
            dataBF = dataBF[dataBF[k].notna()]

        dataQT_notNull = ['SY_SFA_ID_QT', 'STAFF_ID_QT', 'SY_QTTIME_QT']
        for v in dataQT_notNull:
            dataQT = dataQT[dataQT[v].notna()]

        dataBF.to_excel('D:/DataCenter/BFQT/mergeTable_BF_QT/BF/BF_bei.xlsx', index=False)
        dataQT.to_excel('D:/DataCenter/BFQT/mergeTable_BF_QT/QT/QT_bei.xlsx', index=False)

        df1 = pd.read_excel('D:/DataCenter/BFQT/mergeTable_BF_QT/BF/BF_bei.xlsx', sheet_name=0, header=0,
                            index_col=None)
        df2 = pd.read_excel('D:/DataCenter/BFQT/mergeTable_BF_QT/QT/QT_bei.xlsx', sheet_name=0, header=0,
                            index_col=None)

        df1.insert(0, 'indexQD', '')
        for i in range(len(df1['SY_BFTIME_QD'])):
            df1.loc[i, "indexQD"] = str(df1.loc[i, 'SY_BFTIME_QD'])[0:11] + str(df1.loc[i, 'STAFF_ID_QD']) + str(
                df1.loc[i, 'SY_SFA_ID_QD'])[0:9]
        df2.insert(0, 'indexQT', '')
        for j in range(len(df2['SY_QTTIME_QT'])):
            df2.loc[j, 'indexQT'] = str(df2.loc[j, 'SY_QTTIME_QT'])[0:11] + str(df2.loc[j, 'STAFF_ID_QT']) + str(
                df2.loc[j, 'SY_SFA_ID_QT'])[0:9]

        '''
        构造拜访表与签退表唯一的主键
        '''
        # 拜访表唯一主键构造
        df1.insert(1, 'markQD', '')
        for i in range(len(df1['indexQD'])):
            list1 = np.where(df1.loc[:, 'indexQD'] == df1.loc[i, 'indexQD'])[0]
            list2 = np.argsort(list1)
            list_len = len(list1)
            arr_new = []
            for item in list1:
                arr_new.append(item)
            for item in list2:
                arr_new.append(item)
            for j in range(list_len):
                df1.loc[arr_new[j], 'markQD'] = "*" * arr_new[j + list_len]
        df1.insert(0, 'UNIQUE_KEYS', '')
        for i in range(len(df1['indexQD'])):
            df1.loc[i, 'UNIQUE_KEYS'] = str(df1.loc[i, 'indexQD']) + str(df1.loc[i, 'markQD'])
        print("拜访表主键唯一化成功！！！")

        # 签退表唯一主键
        df2.insert(0, 'UNIQUE_KEYS', '')
        for i in range(len(df2['indexQT'])):
            if len(np.where(df1.loc[:, 'indexQD'] == df2.loc[i, 'indexQT'])[0]) <= 1:
                if len(np.where(df1.loc[:, 'indexQD'] == df2.loc[i, 'indexQT'])[0]) == 0:
                    df2.loc[i, 'UNIQUE_KEYS'] = df2.loc[i, 'indexQT']
                else:
                    if len(np.where(df2.loc[:, 'indexQT'] == df2.loc[i, 'indexQT'])[0]) == 1:
                        df1_IndexOver = np.where(df1.loc[:, 'indexQD'] == df2.loc[i, 'indexQT'])[0]
                        end_TimeOver = time.mktime(
                            datetime.datetime.strptime(str(df2.loc[i, 'SY_QTTIME_QT']),
                                                       "%Y-%m-%d %H:%M:%S").timetuple())
                        start_TimeOver = time.mktime(
                            datetime.datetime.strptime(str(df1.loc[df1_IndexOver[0], 'SY_BFTIME_QD']),
                                                       "%Y-%m-%d %H:%M:%S").timetuple())
                        time_DiffOver = end_TimeOver - start_TimeOver
                        if time_DiffOver > 0:
                            df2.loc[i, 'UNIQUE_KEYS'] = df2.loc[i, 'indexQT']
                        else:
                            pass
                    else:
                        if df2.loc[i, 'UNIQUE_KEYS'] != "":  # 之前填充过的唯一索引跳过
                            pass
                        else:
                            df1_IndexNew = np.where(df1.loc[:, 'indexQD'] == df2.loc[i, 'indexQT'])[0]
                            df2_IndexNew = np.where(df2.loc[:, 'indexQT'] == df2.loc[i, 'indexQT'])[0]
                            time_New1 = []
                            for ts1 in df1_IndexNew:
                                time_New1_Diff = df1.loc[ts1, 'SY_BFTIME_QD']
                                time_New1.append(time_New1_Diff)
                            time_New2 = []
                            for ts2 in df2_IndexNew:
                                time_New2_Diff = df2.loc[ts2, 'SY_QTTIME_QT']
                                time_New2.append(time_New2_Diff)
                            for tss in time_New1:
                                df1_NewList = [tss for i in time_New2]
                            new_Null = []
                            for s, ss in zip(time_New2, df1_NewList):
                                end_NewTime = time.mktime(
                                    datetime.datetime.strptime(str(s), "%Y-%m-%d %H:%M:%S").timetuple())
                                start_NewTime = time.mktime(
                                    datetime.datetime.strptime(str(ss), "%Y-%m-%d %H:%M:%S").timetuple())
                                time_NewDiff = end_NewTime - start_NewTime
                                new_Null.append(time_NewDiff)
                            # 全部小于0的情况跳过
                            if max([i for i in new_Null]) < 0:
                                pass
                            else:
                                # 定位出对应的大于等于0中最小的签到表索引
                                pos_NewNum_Min = min([i for i in new_Null if i >= 0])
                                for jj in range(len(new_Null)):
                                    if new_Null[jj] == pos_NewNum_Min:
                                        loc_NewIndex = df2_IndexNew[jj]  # 正数且最小的索引
                                        df2.loc[loc_NewIndex, 'UNIQUE_KEYS'] = df1.loc[df1_IndexNew[0], 'UNIQUE_KEYS']
                                    else:
                                        pass
            else:
                df1_Index = np.where(df1.loc[:, 'indexQD'] == df2.loc[i, 'indexQT'])[0]
                df2_Index = np.where(df2.loc[:, 'indexQT'] == df2.loc[i, 'indexQT'])[0]
                df1_Ser = np.argsort(df1_Index)
                df2_Ser = np.argsort(df2_Index)
                df1_len = len(df1_Ser)
                df2_len = len(df2_Ser)
                time_List1 = []
                for m in df1_Index:
                    time_Diff1 = df1.loc[m, 'SY_BFTIME_QD']
                    time_List1.append(time_Diff1)
                time_List2 = df2.loc[i, 'SY_QTTIME_QT']
                df2_Index_new = [time_List2 for i in time_List1]
                time_Null = []
                for k, kk in zip(df2_Index_new, time_List1):
                    end_Time = time.mktime(datetime.datetime.strptime(str(k), "%Y-%m-%d %H:%M:%S").timetuple())
                    start_Time = time.mktime(datetime.datetime.strptime(str(kk), "%Y-%m-%d %H:%M:%S").timetuple())
                    time_Diff = end_Time - start_Time
                    time_Null.append(time_Diff)
                # 全部小于0的情况跳过
                if max([i for i in time_Null]) < 0:
                    pass
                else:
                    # 定位出对应的大于等于0中最小的签到表索引
                    pos_Num_Min = min([i for i in time_Null if i >= 0])
                    for jj in range(len(time_Null)):
                        if time_Null[jj] == pos_Num_Min:
                            loc_Index = df1_Index[jj]  # 正数且最小的索引
                            df2.loc[i, 'UNIQUE_KEYS'] = df1.loc[loc_Index, 'UNIQUE_KEYS']
        print("签退表主键唯一化成功！！！")
                            
        result = pd.merge(df1.drop_duplicates(), df2.drop_duplicates(), how='left', left_on='UNIQUE_KEYS',
                          right_on='UNIQUE_KEYS')
        # 多级排序，ascending=False代表按降序排序，na_position='last'代表空值放在最后一位
        result.sort_values(by=['UNIQUE_KEYS', 'SY_QTTIME_QT'], ascending=False, na_position='last')
        result.drop_duplicates(subset='UNIQUE_KEYS', keep='last', inplace=True)
        res = result.drop(columns=['indexQD', 'indexQT', 'markQD'])
        print("最后成功匹配签退时间的数据有" + str(len(res)) + "行")
        res.to_excel('D:/DataCenter/BFQT/mergeTable_BF_QT/merge_BF_Table.xlsx', index=False)
        print("最后成功匹配的数据有" + str(len(res)) + "行")
        print("拜访签退表合并成功！！！")
        mtEndTime = datetime.datetime.now()
        print("<合并拜访签退表end>耗时：" + str((mtEndTime - mtStartTime).seconds) + "秒")
    except Exception as e:
        print("拜访签退表合并出错！！！", e)


def uploadMYSQL():
    startTime = datetime.datetime.now()  # 开始计时
    print("开始上传数据库ing......")
    try:
        def mapping_df_types(df):
            dtypedict = {}
            for i, j in zip(df.columns, df.dtypes):
                if "object" in str(j):
                    dtypedict.update({i: NVARCHAR(length=255)})
                if "float" in str(j):
                    dtypedict.update({i: NVARCHAR(length=255)})
                if "int" in str(j):
                    dtypedict.update({i: NVARCHAR(length=255)})

        def get_exce(wei_zhi):
            all_exce = glob.glob(wei_zhi + "*.xlsx")  # 匹配所有xls文件
            print("该目录下有" + str(len(all_exce)) + "个exce文件：")
            if (len(all_exce) == 0):
                return 0
            else:
                for i in range(len(all_exce)):
                    print(all_exce[i])
                return all_exce

        def newdf():
            df = pd.DataFrame(
                columns=['UNIQUE_KEYS', 'MANDT_QD', 'OBJECTI_QD', 'NAME_QD', 'STAFF_DESC_QD', 'SY_DEPT_DESC_QD',
                         'SY_SFA_DESC_QD', 'SY_POINT_DESC_QD', 'F0000003_QD', 'SY_SFA_BINARYCODE_QD', 'SY_TYPE_QD',
                         'SY_SFA_ID_QD', 'SY_BFDATE_QD', 'key_QD', 'CREATEDBY_QD', 'SY_BFTIME_QD', 'MODIFIEDBY_QD',
                         'MODIFIEDTIME_QD', 'CREATEDBYOBJECT_QD', 'OWNERIDOBJECT_QD', 'OWNERDEPTIDOBJECT_QD',
                         'MODIFIEDBYOBJECT_QD', 'SY_LATITUDE_QD', 'SY_LONGITUDE_QD', 'STAFF_ID_QD', 'SY_DEPT_ID_QD',
                         'MANDT_QT', 'OBJECTID_QT', 'NAME_QT', 'STAFF_DESC_SECOND_QT', 'SY_DEPT_DESC_QT',
                         'SY_POINT_DESC_QT', 'SY_PHOTO_QT', 'SY_SFA_BINARYCODE_QT', 'SY_SFA_DESC_QT', 'SY_QTDATE_QT',
                         'XIAOJIE_QT', 'STAFF_DESC_FIRST_QT', 'SY_QTTIME_QT', 'MODIFIEDBY_QT', 'MODIFIEDTIME_QT',
                         'CREATEDBYOBJECT_QT', 'OWNERIDOBJECT_QT', 'OWNERDEPTIDOBJECT_QT', 'MODIFIEDBYOBJECT_QT',
                         'SY_LATITUDE_QT', 'SY_LONGITUDE_QT', 'STAFF_ID_QT', 'SY_DEPT_ID_QT', 'SY_SFA_ID_QT'])
            return df

        all_exce = get_exce("D:\\DataCenter\\BFQT\\mergeTable_BF_QT\\")  # 获取路径下全部xlsx文件
        df = newdf()
        for i in range(len(all_exce)):
            print("加载" + str(all_exce[i]) + "数据ing......")
            df1 = pd.read_excel(all_exce[i], sheet_name=0, dtype=str)  # df-通过表单索引来指定读取的表单，第一个文件第二个表格
            df = df.append([df1])  # 所有数据表合并在df表中
        dtypedict = mapping_df_types(df)  # 转化数据类型
        print("upload数据库ing: alex -> sfa -> sfa_bf_fact")
        engine = create_engine('mysql+pymysql://root:123456@localhost:3306/sfa?charset=utf8')
        df.to_sql('sfa_bf_fact', engine, dtype=dtypedict, index=False, if_exists='replace')  # append/repalce
        endTime = datetime.datetime.now()
        print("<upload数据库end>耗时" + str((endTime - startTime).seconds) + "秒")
    except Exception as eX:
        print("上传数据库出错！！！", eX)


try:
    dataHANA()
    uploadMYSQL()
    allEndTime = datetime.datetime.now()
    print("全部成功end！！！")
    print("总耗时：" + str((allEndTime - allStartTime).seconds) + "秒")
except Exception as eXC:
    print("出错！！！", eXC)
