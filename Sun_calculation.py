from os import mkdir, path
import pandas as pd


class Sun_calculation():

    column_names = ["id", "name", "x", "y", "z", "zone", "spaceName", "area_m2", "K", "orient"]
    
    columns_hours = ["0_1","1_2","2_3","3_4","4_5","5_6","6_7",
                 "7_8","8_9","9_10","10_11","11_12","12_13",
                 "13_14","14_15","15_16","16_17","17_18","18_19",
                 "19_20","20_21","21_22","22_23","23_24"]
    zones: list

    def __init__(self, 
                 path_to_sun_radiationFile:str,
                 path_to_WallsFile:str,
                 zones: list
                 ) -> None:

        self.path_to_WallsFile = path_to_WallsFile

        self.df_sun_radiation = pd.read_csv(path_to_sun_radiationFile, delimiter=';')

        self.df_walls = pd.read_csv(path_to_WallsFile, names=Sun_calculation.column_names)
        self.zones = zones

        self.clearDeleteLater()
        self.prepare_df_panels()
        self.prepare_df_sunrad()

        self.df_merged = self.merge_df_walls_and_sunrad()
        self.df_calculated = self.calculate_heat_surplus()

        self.max_hour = self.find_max_hour().replace('_W', "")


    def clearDeleteLater(self):
        self.df_walls.dropna(inplace=True)
        self.df_walls['zone'] = self.df_walls['zone'].str.replace(" Фонарь", "")
        self.df_walls['zone'] = self.df_walls['zone'].str.replace("Атриум ", "")


    def prepare_df_panels(self):
        self.df_walls.drop(['K', 'x', 'y', 'z'], axis=1, inplace=True)
        self.df_walls = self.df_walls.groupby(['spaceName', 'orient', 'name', 'zone'])['area_m2'].sum().reset_index(name ='area_wall_sum_m2')
        

    def prepare_df_sunrad(self):
        self.df_sun_radiation = self.df_sun_radiation.loc[self.df_sun_radiation['name'].isin(self.df_walls["name"].unique())]
        self.df_sun_radiation = self.df_sun_radiation.loc[self.df_sun_radiation['orient'].isin(self.df_walls["orient"].unique())]


    def merge_df_walls_and_sunrad(self):
        df_merged = pd.merge(self.df_walls, self.df_sun_radiation,  how='left', left_on=['name','orient'], right_on = ['name','orient'])
        df_merged.dropna(inplace=True)
        return df_merged


    def calculate_heat_surplus(self):
        df_calculated = self.df_merged.copy()
        for column_name in Sun_calculation.columns_hours:  
            df_calculated[f'{column_name}_W'] = round(df_calculated["area_wall_sum_m2"] * df_calculated[column_name])
        df_calculated.loc['Total'] = df_calculated.sum(numeric_only=True)

        #create new column with max for every space 

        return df_calculated
    

    def find_max_hour(self):
        df_max_value = self.df_calculated.drop(['spaceName', 'orient', 'name', 'zone', 'area_wall_sum_m2'], axis=1)
        df_max_value.drop(Sun_calculation.columns_hours, axis=1, inplace=True)
        max_heat_surplus_W = df_max_value.max(axis=0)
        
        return  max_heat_surplus_W.idxmax()
    

    def save_csv_zone_max(self):

        for zone_name in self.zones:

            columns_for_drop = self.columns_hours[::]
            columns_for_drop.remove(self.max_hour)

            new_df = self.df_calculated.drop(columns_for_drop, axis=1)

            new_df = new_df.loc[new_df['zone'] == zone_name]
            new_df.index.name = 'id'
            
            folder = f"{self.path_to_WallsFile}".replace(".txt", "")

            if not path.isdir(f"zones --- {folder}"):
                mkdir(f"zones --- {folder}", mode=0o777)

            new_df.to_csv(f"zones --- {folder}/{folder}_zone{zone_name}.csv")

    
    def save_csv_space_max(self):
        
        temp_df_0 = self.df_calculated.drop(['orient', 'name'], axis=1)
        
        spaces_maximum = dict()

        unique_spaces = self.df_calculated["spaceName"].unique()
        for space in unique_spaces:
            temp_df = temp_df_0.loc[self.df_calculated["spaceName"] == space]
            temp_list = []

            for column in temp_df.columns:
                try: 
                    if (temp_df[column].dtype == "float64" and "W" in column):
                        temp_list.append(sum(temp_df[column]))
                except:
                    print("error")

            if (len(temp_list) != 0):
                max_value = max(temp_list)
                spaces_maximum[space] = max_value

        temp_df_0 = temp_df_0.groupby(['spaceName', 'zone'])['area_wall_sum_m2'].sum().reset_index(name ='area_wall_sum_m2')
        temp_df_0.sort_values(["zone"], inplace=True, ignore_index=True)

        try:
            temp_df_0["total_space_heatSurplus_W"] = [spaces_maximum[spacename] for spacename in temp_df_0["spaceName"]]
        except:
            print("error")


        folder = f"spacesMax_heatSurplus --- {self.path_to_WallsFile.replace(".txt", "")}"
        
        if not path.isdir(folder):
            mkdir(folder, mode=0o777)

        temp_df_0.to_csv(f"{folder}/{folder}.csv")
        
        

                



