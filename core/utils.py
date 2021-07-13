import os
import numpy as np
import pandas as pd
from joypy import joyplot
import matplotlib.pyplot as plt
import plotly.graph_objects as go
from plotly.subplots import make_subplots

import warnings
warnings.filterwarnings("ignore")
plt.rcParams['font.size'] = 14
plt.rcParams['font.serif'] = "Cambria"
plt.rcParams['font.family'] = "serif"


def combine_results(df_pFBA, df_FVA):
    '''
    Function to combine the results obtained 
    from pFBA and FVA.
    '''

    # Obtain the reaction types
    df_FVA["Rxn_1_Type"] = df_pFBA["Rxn_1_Class"]
    df_FVA["Rxn_2_Type"] = df_pFBA["Rxn_2_Class"]

    # Rearrange the order of columns
    df_FVA = df_FVA[["Rxn_1", "Rxn_1_Type", "Rxn_1_Min", \
                     "Rxn_1_Max", "Rxn_2", "Rxn_2_Type", \
                     "Rxn_2_Min", "Rxn_2_Max", "v1", "v2"]]
    
    
    # Ensure that the whole dataframe can be printed
    pd.set_option("display.max_rows", None, "display.max_columns", None, "display.expand_frame_repr", False)
    
    return df_FVA

def psl_rsl(df, tol=0):
    # Function to perform PSL/RSL analysis.
    # Ensure that both the minimum fluxes are greater than 0
    mask = (np.abs(df["Rxn_1_Min"])>tol) & (np.abs(df["Rxn_2_Min"])>tol)
    df.loc[mask, "Type"] = "RSL"
    df.loc[~(mask), "Type"] = "PSL"
    
    return df

def get_distribution(df, model):
    # Function to group the dataframe by the reaction types and the pair type
    df_grouped = df.groupby(["Type", "Rxn_1_Type", "Rxn_2_Type"]).count()
    df_grouped = df_grouped.rename(columns={"Rxn_1":"Count", "Rxn_1_Min":"Fraction"})
    df_grouped["Fraction"] /= df_grouped["Fraction"].sum()
    df_grouped.drop(["Rxn_1_Max", "Rxn_2", "Rxn_2_Min", "Rxn_2_Max", "v1", "v2"], axis=1, inplace=True)
    df_grouped.to_csv("../results/"+model+"/"+model+"_PSL_RSL_distribution.csv")
    df_grouped.reset_index(inplace=True)
    return df_grouped

def plot_results(df, model):
    # Function to plot the results
    df["Combination"] = df["Rxn_1_Type"] + ", " + df["Rxn_2_Type"]

    psl_df = df.loc[df["Type"]=="PSL",:]
    rsl_df = df.loc[df["Type"]=="RSL",:]
    
    fig = make_subplots(rows=1, cols=2, subplot_titles=("PSL", "RSL"), \
                        specs=[[{"type": "domain"}, {"type": "domain"}]])
    
    fig.add_trace(go.Pie(labels=psl_df["Combination"], values=psl_df["Fraction"]*100, \
                         hole=0.4),row=1, col=1)
    fig.add_trace(go.Pie(labels=rsl_df["Combination"], values=rsl_df["Fraction"]*100, \
                         hole=0.4),row=1, col=2)

    fig.update_layout(title_text="Model: "+model)
    image_name = "../results/images/"+model+"_PSL_RSL_dist.png"
    fig.write_image(image_name)
    fig.show()
    
    df_new = df.groupby(["Type"]).sum()
    # Ensure that order is PSL, RSL
    df_new.sort_index(inplace=True)
    count = df_new["Count"]
    fraction = df_new["Fraction"]
    
    return count, fraction

# def color_tagging(df):
#     # Function to plot the results
#     df["Combination"] = df["Rxn_1_Type"] + ", " + df["Rxn_2_Type"]
#     print(df["Combination"].unique())
#     ZeroFlux_Rxns, pFBAOpt_Rxns
    
#     color_dict = {'ZeroFlux_Rxns, pFBAOpt_Rxns':'#e6f2ff', '2':'#99ccff', '3':'#ccccff',
#               '4':'#cc99ff', '5':'#ff99ff', '6':'#ff6699', 
#               '7':'#ff9966', '8':'#ff6600', '9':'#ff5050', 
#               '10':'#ff0000'}
    
#     ['' 'pFBAOpt_Rxns, ELE_Rxns', 'pFBAOpt_Rxns, MLE_Rxns' 'pFBAOpt_Rxns, pFBAOpt_Rxns']
    
#     colors = np.array([''] * len(crit), dtype = object)
#     for i in np.unique(crit):
#         colors[np.where(crit == i)] = color_dict[str(i)]

def get_diff(val):
    list_value = []
    for i in val:
        list_value.append(np.sum(np.sign(i)))
    
    return list_value

def get_net_diff(val):
    list_value = []
    for i in val:
        list_value.append(np.sum(i))
        
    return list_value

def get_dataframes0(name, models, columns, norm='L0'):
    df = pd.DataFrame()
    for i in columns:
        fname = '../examples/' + name + '/' + name + '_' + i + '_L0.csv'
        fin = open(fname)
        data = fin.read().splitlines()
        fin.close()
        
        df[i] = data[1:]
        df['num_'+i] = df[i].str.split(',').apply(len)
        
    df.loc[df['PathShort']=="", 'num_PathShort'] = 0
    df.loc[df['PathLong']=="", 'num_PathLong'] = 0
    df.loc[df['pathCommon']=="", 'num_pathCommon'] = 0
    df = df.drop(['num_solStatus', 'num_diff'], axis=1)
    df = df.rename(columns={'num_PathShort':'L0_num_PathShort', 
                            'num_PathLong':'L0_num_PathLong', 
                            'num_pathCommon':'L0_num_pathCommon',
                            'num_rxns':'L0_num_rxns'})
    return df

def get_dataframes1(name, models, columns, norm='L0'):
    df = pd.DataFrame()
    for i in columns:
        fname = '../examples/' + name + '/' + name + '_' + i + '_L1.csv'
        fin = open(fname)
        data = fin.read().splitlines()
        fin.close()
        
        df[i] = data[1:]
        df['num_'+i] = df[i].str.split(',').apply(len)
        
    df.loc[df['PathShort']=="", 'num_PathShort'] = 0
    df.loc[df['PathLong']=="", 'num_PathLong'] = 0
    df.loc[df['pathCommon']=="", 'num_pathCommon'] = 0
    df = df.drop(['num_solStatus', 'num_diff'], axis=1)
    df = df.rename(columns={'num_PathShort':'L1_num_PathShort', 
                            'num_PathLong':'L1_num_PathLong', 
                            'num_pathCommon':'L1_num_pathCommon',
                            'num_rxns':'L1_num_rxns'})
    return df

def preprocess(data):
    df = pd.DataFrame(data, columns=["rxns", "diff_flux", "abs_diff_flux", \
                                     "PathShort", "PathLong", "pathCommon", \
                                     "del_rxn1", "del_rxn2", "totalFluxDiff",\
                                     "solStatus"])

    # Get the reactions
    rxns = df["rxns"]
    new_rxns = []
    for i in rxns:
        temp = []
        for j in i:
            temp.append(str(j[0][0]))
        new_rxns.append(temp)
        
    df["rxns"] = new_rxns

    # Get reaction 1
    del_rxn1 = df["del_rxn1"]
    new_del_rxn1 = []
    for i in del_rxn1:
        new_del_rxn1.append(i[0][0][0])
    df["del_rxn1"] = new_del_rxn1

    # Get reaction 2
    del_rxn2 = df["del_rxn2"]
    new_del_rxn2 = []
    for i in del_rxn2:
        new_del_rxn2.append(i[0][0][0])
    df["del_rxn2"] = new_del_rxn2

    # Get flux difference
    diff_flux = df["diff_flux"]
    new_diff_flux = []
    for i in diff_flux:
        temp = []
        for j in i:
            temp.append(j[0])
        new_diff_flux.append(temp)
        
    df["diff_flux"] = new_diff_flux

    # Get absolute flux difference
    abs_diff_flux = df["abs_diff_flux"]
    new_abs_diff_flux = []
    for i in abs_diff_flux:
        temp = []
        for j in i:
            temp.append(j[0])
        new_abs_diff_flux.append(temp)
        
    df["abs_diff_flux"] = new_abs_diff_flux

    # Get PathShort
    PathShort = df["PathShort"]
    new_PathShort = []
    for i in PathShort:
        temp = []
        for j in i:
            temp.append(str(j[0][0]))
        new_PathShort.append(temp)
        
    df["PathShort"] = new_PathShort
    
    # Get PathLong
    PathLong = df["PathLong"]
    new_PathLong = []
    for i in PathLong:
        temp = []
        for j in i:
            temp.append(str(j[0][0]))
        new_PathLong.append(temp)
        
    df["PathLong"] = new_PathLong
    
    # Get pathCommon
    pathCommon = df["pathCommon"]
    new_pathCommon = []
    for i in pathCommon:
        temp = []
        for j in i:
            temp.append(str(j[0][0]))
        new_pathCommon.append(temp)
        
    df["pathCommon"] = new_pathCommon
    
    # Get totalFluxDiff
    totalFluxDiff = df["totalFluxDiff"]
    new_totalFluxDiff = []
    for i in totalFluxDiff:
        new_totalFluxDiff.append(i[0][0])
        
    df["totalFluxDiff"] = new_totalFluxDiff

    # Get solStatus
    solStatus = df["solStatus"]
    new_solStatus = []
    for i in solStatus:
        new_solStatus.append(i[0][0])
        
    df["solStatus"] = new_solStatus

    sl_size = [len(i) for i in df["rxns"]]
    df["sl_size"] = sl_size

    common_sl_size = [len(i) for i in df["pathCommon"]]
    df["common_sl_size"] = common_sl_size
    df["num_diff"] = get_diff(df["diff_flux"])
    df["net_diff"] = get_net_diff(df["diff_flux"])
    

    return df

def plot_ridge_lines(df, y, means, figname="", title="", xlabel="", ylabel="", means_flag=True, color="#686de0", alpha=1):
    
    fig, axes = joyplot(data=df, by=y, linecolor=color, \
                        alpha=alpha, fill=False, figsize=(12, 8), \
                        grid="y")

    if means_flag:
        for i in range(len(means)):
            ymin = 0
            mean = means[i]
            
            try:
                yval = axes[i].lines[0].get_ydata()[np.where(np.round(axes[i].lines[0].get_xdata(),2) == np.around(mean, 1))[0][0]]
                axes[i].plot([mean,mean], [ymin, yval], color="red", zorder=200) 

            except:
                # ymax = axes[i].lines[0].get_ydata().max()
                # axes[i].plot([means[i]] * 2, [ymin, ymax], color="red", zorder=200)
                yval = axes[i].lines[0].get_ydata()[np.where(np.round(axes[i].lines[0].get_xdata(), 0) == np.around(mean, 0))[0][0]]
                axes[i].plot([mean,mean], [ymin, yval], color="red", zorder=200) 
            # need to set a high zorder to draw them in front of all the rest

    col = [i for i in df.columns if i!="Organism"]
    col = col[0]
    print(df[col].min(), df[col].max())
    axes[-1].set_xlim(df[col].min(), df[col].max())
    plt.title(title, fontsize=20)
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.grid()
    plt.savefig(figname)
    plt.show()