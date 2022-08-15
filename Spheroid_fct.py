# -------------------------------
# rec.py
# Author: FelixRomer
# Email: felix.lucas.romer@gmail.com
# Date: 2022/07/29
# -------------------------------

import pandas as pd
import numpy as np
import seaborn as sns
import functools
import matplotlib.pyplot as plt

'''Ich überlege gerade noch zu den mean listen eine Splae mit Experimant namen zu machen'''
def Excel_file_sheet_reader(file):
    xlsx_file = pd.ExcelFile(file)
    sheets = xlsx_file.sheet_names
    df=pd.DataFrame()
    for i, j in zip(sheets, np.arange(0,len(sheets))):
        df_sheet = pd.read_excel(file, sheet_name=i)
        df_sheet['day']=j
        df=pd.concat([df,df_sheet],axis=0)
    df.sort_values(['day','Well'], inplace=True)
    df.reset_index(drop=True, inplace=True)
    return df

def DataFrame_adapter(df, Korrekturfaktor, Experiment_name):
    df=df.iloc[:,[0,2,3,4,5,6,7,8,9,19]]
    df['Länge_ÜS']=df.loc[:,'Length']/Korrekturfaktor
    df['Breite_ÜS']=df.loc[:,'Width']/Korrekturfaktor
    df['Fläche_berechnet']=(df.loc[:,'Länge_ÜS']/2)*(df.loc[:,'Breite_ÜS']/2)*np.pi
    df['Volumen_berechnet']=0.5*df.loc[:,'Länge_ÜS']*(df.loc[:,'Breite_ÜS']**2)
    df['roundness']=df.loc[:,'Breite_ÜS']/df.loc[:,'Länge_ÜS']
    df['Experiment']=Experiment_name
    return df


def mean_calculater(df, df_drop, Col, Experiment_name,Bed_unique):
    mean_list=[]
    for i in df['day'].unique():
        day_list=[]
        for bedingung in Bed_unique:
            search_value=df_drop[(df_drop['day']==i)&(df_drop['Bedingung']==bedingung)][Col].mean()
            day_list.append(search_value)
        mean_list.append(day_list)
    mean_df=pd.DataFrame(mean_list, columns=Bed_unique)
    mean_df['Experiment']=Experiment_name
    return mean_df


def diff_to_mean(df, mean_df, Col,Bed_unique):
    #find a rep well per Condition on the Volumen 
    # add column with differnece to the mean to df
    mean_liste=[]
    for day in df['day'].unique():
        for bed in Bed_unique:
            for n in np.arange(0, (96/len(Bed_unique))):
                mean_liste.append(mean_df.loc[day,bed])
    df[f"mean_{Col}"]=mean_liste
    df[f"diff_{Col}"]=(df[Col]-df[f"mean_{Col}"]).abs()
    return df
    
def rep(df_adapt):
    df_adapt['repressentation']=df_adapt['diff_Fläche_berechnet']*df_adapt['diff_roundness']
    return df_adapt

def well(df_rep, drop_args):    
    # df_well holds the mean diff to the mean Vol per well 
    df_well=pd.DataFrame(df_rep[~(df_rep.Bemerkung.isin(drop_args))].groupby('Well')['repressentation'].mean())
    
    return df_well

def drop_rows(df_well, drop_args):
    df_drop=df_well.loc[~(df_well.Bemerkung.isin(drop_args))]
    droped_well=df_well.loc[df_well.Bemerkung.isin(drop_args)]
    end_wells=list(droped_well[droped_well['day']==(len(df_drop['day'].unique())-1)]['Well'])
    return df_drop, end_wells

def print_result(df_adapt,df_well, end_wells,Experiment_name,Bed_unique):
#final result is printet per condition
    
    
    k=int(96/len(Bed_unique))
    list_1=[['Condition', 'most representativ Well', 'repressentation factor']]
    for n in np.arange(0,len(Bed_unique)):
        list_2=[]
        df_temp=df_well.loc[n*k+1:(n+1)*k]
        df_temp=df_temp[~(df_temp.index.isin(end_wells))]
        df_temp.reset_index(inplace=True)
        arg_min=np.argmin(df_temp['repressentation'])
        min_diff=df_temp.iloc[arg_min]['repressentation']
        well=int(df_temp.iloc[arg_min]['Well'])
        list_1.append([Bed_unique[n], well, min_diff])
        
        print('The most representativ well for Condition', Bed_unique[n], 'is well', well, '.')
        print('The mean difference to the mean Volumen times the mean difference to the mean roundness is', min_diff)
        print('---')
    rep_wells=pd.DataFrame(list_1[1:],columns=list_1[0])
    rep_wells['Experiment']=Experiment_name
    return rep_wells

def rep_well_finder(file,Experiment_name ,Bed_unique,Correction_factor=1000,drop_args = []):
    df=Excel_file_sheet_reader(file)
    df_adapt=DataFrame_adapter(df, Correction_factor,Experiment_name)
    df_drop, end_wells=drop_rows(df_adapt, drop_args)
    mean_area=mean_calculater(df_adapt, df_drop, 'Fläche_berechnet',Experiment_name,Bed_unique)
    mean_round=mean_calculater(df_adapt,df_drop, 'roundness',Experiment_name,Bed_unique)
    df_diff_0=diff_to_mean(df_adapt, mean_area, 'Fläche_berechnet',Bed_unique)
    df_diff=diff_to_mean(df_diff_0, mean_round, 'roundness',Bed_unique)
    df_rep=rep(df_diff)
    df_well=well(df_rep, drop_args)
    rep_wells=print_result(df_adapt,df_well, end_wells, Experiment_name,Bed_unique)
    return rep_wells,df_well, df_rep,df_diff, mean_round, mean_area,df_drop, df_adapt, end_wells

def multi_experiment_well_finder(file_list,Experiment_name,Bed_unique,Correction_factor=1000,drop_args = []):
    mean_round_extended=pd.DataFrame()
    mean_area_extended=pd.DataFrame()
    rep_well_extended=pd.DataFrame()
    df_adapt_extendet=pd.DataFrame()
    for file,Experiment in zip(file_list,Experiment_name):
        rep_wells,df_well, df_rep,df_diff, mean_round, mean_area,df_drop, df_adapt, end_wells \
        =rep_well_finder(file,Experiment ,Bed_unique,Correction_factor,drop_args)
        mean_round_extended=mean_round_extended.append(mean_round)
        mean_area_extended=mean_area_extended.append(mean_area)
        rep_well_extended=rep_well_extended.append(rep_wells)
        df_adapt_extendet=df_adapt_extendet.append(df_adapt)
    return mean_round_extended,mean_area_extended,rep_well_extended, df_adapt_extendet
    
        
  


def roundplotfunc(mean_extended, Cell,Stat, color_palette=['#000000','#b3ffb3','#006600','#0000e6','#3366ff', '#ff0000', '#ffa500','#990000'],sharey=True,sharex=True):
    mean_extended.index.name = 'Day'
    mean_a=mean_extended.groupby('Day').mean()

    mean_a['Experiment']='Mean'
    mean_extended=mean_extended.append(mean_a)
    mean_extended.reset_index(inplace=True)
    melt_round=mean_extended.melt(id_vars=['Day', 'Experiment'],var_name='Condition', value_name=Stat)

    sns.set_context('talk')
    fig=plt.figure(figsize=(10,10))
    

    fig=sns.relplot(data=melt_round,
                    x='Day',
                    y=Stat,
                    hue='Condition',
                    palette=color_palette,
                    col='Experiment',
                    kind='line',
                    facet_kws={'sharey':sharey, 'sharex':sharex}
    )
    fig.fig.suptitle(f'Mean {Stat} of {Cell} Cells', y=1.07,x=0.44, size = 20)
    fig.set_titles('{col_name}',y=1.05)

    sns.move_legend(fig, "lower center", bbox_to_anchor=(0.44, -0.25),ncol=4, frameon=False)
    return fig