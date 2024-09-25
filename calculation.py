import numpy as np
import pandas as pd 
from matplotlib import pyplot as plt 
from matplotlib import figure, use



def prepare_panels(raw_df: pd.DataFrame, zone:str):
    new_df = raw_df.drop(['K', 'x', 'y', 'z'], axis=1)
    new_df = new_df.groupby(['spaceName', 'orient', 'name', 'zone'])['area'].sum().reset_index(name ='area_wall_sum')
    new_df = new_df.drop(new_df[new_df.zone != zone].index )

    return new_df


def prepare_sun_rad_for_special_zone(raw_sun_df: pd.DataFrame,
                                     df_zone_sorted: pd.DataFrame):

    not_drop_list_panels = []
    not_drop_list_orient = []

    for index, row in df_zone_sorted.iterrows():
        not_drop_list_panels.append(row['name'])
        not_drop_list_orient.append(row['orient'])

    new_sun_df = raw_sun_df.loc[raw_sun_df['name'].isin(not_drop_list_panels)]
    new_sun_df = new_sun_df.loc[new_sun_df['orient'].isin(not_drop_list_orient)]

    return new_sun_df


def merge_panels_and_sunrad(df_panels: pd.DataFrame, df_sun_rad: pd.DataFrame):
    
    new_df = pd.merge(df_panels, df_sun_rad,  how='left', left_on=['name','orient'], right_on = ['name','orient'])
    new_df = new_df.dropna()

    return new_df  


def calculate_heatsurplus(merged_df: pd.DataFrame, columns_hours: list):
    
    for column_name in columns_hours:  
        merged_df[f'{column_name}_W'] = round(merged_df.area_wall_sum * merged_df[column_name])
    merged_df.loc['Total'] = merged_df.sum(numeric_only=True)

    #create new column with max for every space 

    return merged_df


def find_max_hour(df: pd.DataFrame, columns_hours):

    df_max_value = df.drop(['spaceName', 'orient', 'name', 'zone', 'area_wall_sum'], axis=1)
    df_max_value.drop(columns_hours, axis=1, inplace=True)

    max_heat_surplus_W = df_max_value.max(axis=0)
    
    return  max_heat_surplus_W.idxmax()


def prepare_df_to_plot(df: pd.DataFrame):

    new_col = []
    for index, row in df.iterrows():
        
        if type(row['zone']) != str:
            new_col.append('Total')
        else:
            new_col.append(str(row['zone'])+"_"+str(row['spaceName'])+"_"+str(row['name'])+"_"+str(row['orient']))

    new_df = df.drop([i for i in df.columns if "W" not in i], axis=1)

    new_df['name'] = new_col
    new_df = new_df.set_index('name', drop=True)
    new_df = new_df.T
    
    return new_df


def plot_df(df: pd.DataFrame, name_output: str, y_limit:int, y_step:int):

    plt.ioff()

    # Create a new figure, plot into it, then close it so it never gets displayed
    fig = plt.figure()

    plt.figure(figsize=(24, 12), dpi=80)

    plt.xticks([i for i in range(24)])
    plt.yticks([i for i in range(0, y_limit, y_step)])

    # plt.plot(df.index, df['Total'], "-", label='Теплопоступления сумма, Вт')

    for column in df.columns:
        plt.plot(df.index, df[column], "-", label=f'Теплопоступления {column}, Вт')


    plt.title(f"Теплопоступления в зоне по часам - {name_output}")
    plt.xlabel('Часы суток')
    plt.ylabel('Теплопоступления, Вт')
    plt.grid(True)
    plt.legend()
    plt.savefig(name_output)
    plt.close(fig)


def calculate_zone(raw_df_panels: pd.DataFrame, 
                   input_zone:str, 
                   df_sun_radiation: pd.DataFrame, 
                   columns_hours:list, 
                   output_csv_name:str
                   ):
    
    df_panels_prepared = prepare_panels(raw_df_panels, input_zone)
    df_sun_specific = prepare_sun_rad_for_special_zone(df_sun_radiation, df_panels_prepared)
    merged_df = merge_panels_and_sunrad(df_panels_prepared, df_sun_specific)
    new_df = calculate_heatsurplus(merged_df, columns_hours)
    max_hour = find_max_hour(new_df, columns_hours).replace('_W', "")

    columns_for_drop = columns_hours[::]
    columns_for_drop.remove(max_hour)

    new_df.drop(columns_for_drop, axis=1, inplace=True)
    new_df.index.name = 'id'

    new_df.to_csv(output_csv_name)

    return new_df


