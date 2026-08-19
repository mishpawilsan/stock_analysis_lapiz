import requests
import pandas as pd
pd.set_option('display.max_columns', None)
github_api_url = "https://api.github.com/repos/squareshift/stock_analysis/contents/"
response = requests.get(github_api_url)
files = response.json()
csv_files = [file['download_url'] for file in files if file['name'].endswith('.csv')]
# print(csv_files)
# a=csv_files[0]
csv_file = csv_files.pop()
d = pd.read_csv(csv_file)
# print(d.columns)
# print(d)
# print(d.columns)
# print(d.head())
# print(d.tail())
# print(d.shape)
# print(d.describe())
dataframes=[]
file_names=[]
for url in csv_files:
    file_name = url.split("/")[-1].replace(".csv", "")
    df = pd.read_csv(url)
    df['Symbol'] = file_name
    dataframes.append(df)
    file_names.append(file_name)
# print(file_names)
# print(dataframes)
combined_df = pd.concat(dataframes, ignore_index=True)
# print(combined_df)
o_df = pd.merge(combined_df,d,on='Symbol',how='left')
# print(o_df)
result = o_df.groupby("Sector").agg({'open':'mean','close':'mean','high':'max','low':'min','volume':'mean'}).reset_index()
# print(o_df["timestamp"])
o_df["timestamp"] = pd.to_datetime(o_df["timestamp"])
filtered_df = o_df[(o_df['timestamp'] >= "2021-01-01") & (o_df['timestamp'] <= "2021-05-26")]
result_time = filtered_df.groupby("Sector").agg({'open':'mean','close':'mean','high':'max','low':'min','volume':'mean'}).reset_index()
list_sector = ["TECHNOLOGY","FINANCE"]
result_time1 = result_time[result_time["Sector"].isin(list_sector)].reset_index(drop=True)
# print(result_time1)
result_time1.columns = ['Sector','sector_open_mean','sector_close_mean','sector_high','sector_low','sector_volume_mean']
# print(result_time1)
path=r"C:\Users\jsmfo\OneDrive\Documents\stock_code\output_code"
result_time1.to_csv(path,header=True)
print("data has been written successfully")

