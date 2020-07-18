import os
import MT_Clutch_Tools_v1
import pickle

mt_tool = MT_Clutch_Tools_v1.MT_Clutch_Tools()

os.chdir("D:\\Summer_Tasks_20\\IPM_On_Cluster_Files\\11x11_Initial_Sense_Run\\initial_deriv")
print(os.getcwd())


input_list = []
for file in os.listdir():
    if file.endswith(".inp"):
        print(file)
        input_list.append(file)

sdf_dict = mt_tool.combine_multiple_sdf_dicts_into_one(input_list)

for location in sdf_dict:
    print(location)
    for isotope in sdf_dict[location]:
        print(isotope, sdf_dict[location][isotope])



pickle_out = open("tsunami_betas", "wb")
pickle.dump(sdf_dict, pickle_out)

pickle_out = open("tsunami_keff", "wb")
pickle.dump("0.82940", pickle_out)