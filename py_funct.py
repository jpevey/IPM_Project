import os
import collections
import pickle
import scale_file_handler
from datetime import datetime
import time
import MT_Clutch_Tools_v1


def evaluate_1d_cyl(proposed_betas):
    sfh = scale_file_handler.scale_file_handler()
    ### reading in current job information
    current_tsunami_job = tsunami_job_object(sfh, proposed_betas)

    ### This function returns the percent change from the tsunami case given the betas
    proposed_changes = current_tsunami_job.get_beta_percent_change(proposed_betas)
    current_tsunami_job.proposed_changes = proposed_changes
    print("current_tsunami_job.proposed_changes", current_tsunami_job.proposed_changes)
    #### Saving proposed changes to file
    # save_to_file('past_beta_changes', current_summed_changes)
    #
    #### Acting based on the current_summed_changes list
    #### Returns the keff value and the type of evaluation used to get it
    #### can be 'tsunami', 'keno', 'linear_approximation'
    #### print out the linearly predicted keff along with acctual k either with keno or tsunami

    if current_tsunami_job.by_default_run_keno == 'True':
        current_tsunami_job.evaluate_current_step_run_keno_first()
    else:
        current_tsunami_job.evaluate_current_step()

    #### saving current job data to file
    #### add timestamp to output
    # save_data_to_outputcsv()

    current_tsunami_job.write_to_csv()

    ### Mulitpliying all sensitivities by -1, because using fmincon in matlab
    print(current_tsunami_job.tsunami_keff)
    negative_sensitivities = [float(x * -1 * float(current_tsunami_job.tsunami_keff)) for x in
                              current_tsunami_job.beta_sensitivities]

    ### Turning the sensitivities into a matlab array
    # negative_sensitivities_ml = matlab.double(negative_sensitivities)

    #### returning negative keff and sensitivities

    return float(current_tsunami_job.keff) * -1, negative_sensitivities


class tsunami_job_object:
    def __init__(self, sfh, proposed_betas):
        self.sfh = sfh
        self.proposed_betas = proposed_betas

        ### Reading in options file
        self.read_in_options('options.csv')
        ### Populating default values
        print("Reading in default values")
        self.create_default_tsunami_object()

        ### Setting default necluster scale scripts
        self.multithreaded_scale_script = \
            """#!/bin/bash
            #PBS -q gen5
            #PBS -V
            #PBS -l nodes=3:ppn=8
            
            module unload mpi
            module load openmpi/1.8.8-gnu
            module load scale/dev
            cat ${PBS_NODEFILE}
            #NP=$(grep -c node ${PBS_NODEFILE})
            
            cd $PBS_O_WORKDIR
            
            #echo $NP
            scalerte -m -N 24 -M ${PBS_NODEFILE} -T /home/tmp_scale/$USER/scale.$$ %%%input_flag%%%.inp
            grep -a "final result" %%%input_flag%%%.inp.out > %%%input_flag%%%.inp_done.dat
            """
        self.singlethreaded_scale_script = \
            """#!/bin/bash
            
            #PBS -q corei7
            #PBS -V
            #PBS -l nodes=1:ppn=1
            
            module load scale/6.2.3
            
            cd $PBS_O_WORKDIR
            
            scalerte -m %%%input_flag%%%.inp
            grep -a "final result" %%%input_flag%%%.inp.out > %%%input_flag%%%.inp_done.dat"""

        ### Looks for the running output file as described in the options file, 
        ### if it is not there one is created for this new job
        found_tsunami_output = False
        for file in os.listdir("."):
            if self.output_file_string == file:
                print("Found an output file, reading in data from it!")
                found_tsunami_output = True

            ### If a single threaded tsunami job has been run, pull in those sensitivities
            if self.multithreaded_clutch_on_necluster == 'False':
                if self.sdf_file == file:
                    print("Found new sdf file! Overwriting default")
                    self.tsunami_keff, _ = self.sfh.get_keff_and_uncertainty("tsunami_run_.out")

                    ### Reading in tsunami sensitivities
                    self.update_sensitivities("tsunami_run_.sdf")

                    print("Betas before and after reading in from pickle")
                    print(self.tsunami_betas)
                    ### Reading in tsunami betas from pickle 
                    self.read_in_pickle(pickle_file_string='tsunami_betas', read_in_as_attribute='tsunami_betas')
                    print(self.tsunami_betas)
            ### If a MT tsunami job has been run, pull in those sensitivities
            if self.multithreaded_clutch_on_necluster == 'True':
                if self.sensitivity_dict_mt_tsunami == file:
                    print("Loading in", self.sensitivity_dict_mt_tsunami, "sensitivites")
                    self.read_in_pickle(pickle_file_string=self.sensitivity_dict_mt_tsunami,
                                        read_in_as_attribute='sensitivities')
                    print("self.sensitivities", self.sensitivities)
                    print("self.sensitivity_dict_mt_tsunami", self.sensitivity_dict_mt_tsunami)
                    self.combine_sensitivities_by_list()

        if found_tsunami_output == False:
            ### Creating the output file
            self.create_output_csv()

    def read_in_options(self, options_file_string):
        options_file = open(options_file_string, 'r')
        for line in options_file:
            if line.startswith('#'):
                continue

            line = line.strip()
            line_split = line.split(',')
            print(line_split)
            value = line_split[1].strip()

            ### If this value is a list of values, creating a list from input
            if '#' in value:
                value_list = []
                line_split_2 = line_split[1].split('#')
                for val in line_split_2:
                    value_list.append(val)
                value = value_list
            # print(line_split[0].strip(), value)
            try:
                value = value.strip()
            except:
                pass
            setattr(self, line_split[0].strip(), value)

    def read_in_pickle(self, pickle_file_string, read_in_as_attribute):
        pickle_in = open(pickle_file_string, 'rb')
        setattr(self, read_in_as_attribute, pickle.load(pickle_in))

    def write_out_pickle(self, pickle_file_string, write_out_attribute):
        pickle_out = open(pickle_file_string, "wb")
        pickle.dump(getattr(self, write_out_attribute), pickle_out)

    def create_default_tsunami_object(self):
        print("Using default tsunami object")
        self.tsunami_betas = [0.9, 0.9, 0.9, 0.9, 0.9,
                              0.9, 0.9, 0.9, 0.9, 0.9,
                              0.9, 0.9, 0.9, 0.9, 0.9,
                              0.9, 0.9, 0.9, 0.9, 0.9]
        self.tsunami_keff = 0.17738
        self.update_sensitivities("tsunami_rerun_1_.sdf")

    def create_output_csv(self):
        print("Creating output csv file:", self.output_file_string)
        output_csv = open(self.output_file_string, 'w')
        header_string = ''
        # print(self.output_csv_file_headers)
        for header in self.output_csv_file_headers:
            if '*' in header:
                header_ = header.split('*')
                for _ in range(int(header_[1])):
                    header_string += header_[0] + '_' + str(_) + ','

                continue
            header_string += header + ","

        output_csv.write(header_string + '\n')
        output_csv.close()

    def write_to_csv(self):
        print("Writing to output csv file:", self.output_file_string)
        output_csv = open(self.output_file_string, 'a')

        output_string = ""
        for header in self.output_csv_file_headers:
            # print("header:", header)
            output_string += self.create_header_string(header) + ","

        output_csv.write(output_string[:-1] + "\n")
        output_csv.close()

    def evaluate_current_step(self):
        print("Evaluating current step")
        # print(self.proposed_changes)
        max_proposed_change = 0.0
        for material_loc in self.proposed_changes:
            for value in material_loc:
                if abs(value) > max_proposed_change:
                    max_proposed_change = abs(value)
        print("max of proposed change:", max_proposed_change)

        keff = 0.0
        sensitivities = []

        self.linear_keff = self.linear_approximation_of_keff()

        ### If below keno threshould, solve linearly
        if max_proposed_change < float(self.keno_threshold):
            self.beta_sensitivities = self.calculate_sensitivities_2_materials_general()
            self.keff = self.linear_keff
            self.solver_type = 'linear'
            return keff, 'linear'

        ### If above keno threshold, run keno
        if max_proposed_change < float(self.tsunami_threshold):
            keff = self.scale_solve('keno')
            self.beta_sensitivities = self.calculate_sensitivities_2_materials_general()
            self.keff = keff
            self.solver_type = 'keno'
            return keff, 'keno'

        ### If above tsunami threshold, run with tsunami
        if max_proposed_change >= float(self.tsunami_threshold):
            keff = self.scale_solve('tsunami')
            self.update_sensitivities("tsunami_run_.sdf")
            self.beta_sensitivities = self.calculate_sensitivities_2_materials_general()
            self.keff = keff
            self.solver_type = 'tsunami'
            return keff, 'tsunami'

    def evaluate_current_step_run_keno_first(self):
        print("Evaluating current step, keno first")
        # print(self.proposed_changes)
        max_proposed_change = 0.0
        for material_loc in self.proposed_changes:
            for value in material_loc:
                if abs(value) > max_proposed_change:
                    max_proposed_change = abs(value)
        print("max of proposed change:", max_proposed_change)

        keff = 0.0
        sensitivities = []

        ### Solving for k linearly with current tsunami sensitivities
        self.linear_keff = self.linear_approximation_of_keff()
        self.original_linear_keff = self.linear_keff

        ### If below keno threshould for % change in beta, returning
        ### linear keff
        if max_proposed_change < float(self.keno_threshold):
            print("Proposed change (hopefully) linear. Threshold:", self.keno_threshold)
            self.keff = self.linear_keff
            self.keno_keff = 'N/A'
            self.beta_sensitivities = self.calculate_sensitivities_2_materials_general()
            self.solver_type = 'linear'
            return keff, 'linear'

        ### Solving for k with keno
        keff = self.scale_solve('keno')
        self.beta_sensitivities = self.calculate_sensitivities_2_materials_general()
        self.keff = keff
        self.keno_keff = keff
        self.solver_type = 'keno'

        percent_diff_k = abs(float(self.keff) / float(self.linear_keff) - 1)
        print("Percent difference from keno and linear k:", percent_diff_k)

        if self.run_tsunami_every_step == 'True':
            print("Forcing tsunami to run due to options file: run_tsunami_every_step")
            percent_diff_k = 1000000.

        if percent_diff_k >= float(self.default_run_tsunami_keff_percentage_threshold):
            print("Keno keff and linear keff approx differ by: ", percent_diff_k, "Running Tsunami!")
            keff = self.scale_solve('tsunami')

            print("Keno keff and linear keff approx differ by: ", percent_diff_k, "Running Tsunami!")

            print("Ran tsunami, updating beta values, sens. and k/beta sens.")
            ### Updating tsunami beta values
            self.tsunami_betas = self.proposed_betas

            ### Writing out betas to pickle
            self.write_out_pickle(pickle_file_string='tsunami_betas', write_out_attribute='tsunami_betas')

            ### Updating the beta sensitivities from new sdf or combined sdf file
            self.beta_sensitivities = self.calculate_sensitivities_2_materials_general()

            self.tsunami_keff = keff
            self.solver_type += '_tsunami_oldlinkeff:_' + str(self.linear_keff) + '_'

            ### Updating linear approximation of k
            self.linear_keff = self.linear_approximation_of_keff()
            return keff, 'tsunami'

        return keff, 'keno'

    def scale_solve(self, solve_type):
        if self.debug_run_scale == 'False':
            print("Skipping scale calculation")
            return 99.99
        print("SOLVING WITH SCALE")
        if solve_type == 'keno':
            template_file_string = self.kenov_template_filename
            file_name_flag = self.keno_filename_flag
        if solve_type == 'tsunami':
            template_file_string = self.tsunami_template_filename
            file_name_flag = self.tsunami_filename_flag

        keff = 0.0
        ### Solving MT tsunami

        ###   Building inputs

        ### Build scale input
        material_betas = self.proposed_betas
        scale_handler = self.sfh

        ### Building material dictionaries based on options file
        default_material_list = self.build_material_dictionaries

        self.build_scale_input_from_beta(scale_handler,
                                         material_betas=material_betas,
                                         material_1=default_material_list[0],
                                         material_2=default_material_list[1],
                                         flag="%material_replace%",
                                         flag_replacement_string='replace',
                                         template_file_string=template_file_string,
                                         file_name_flag=file_name_flag)

        if self.scale_solver == 'local':
            ### Run scale file
            print("Running: ", file_name_flag + '.inp')

            print("Ran: ", file_name_flag + '.inp')

        if self.scale_solver == 'necluster':
            if solve_type == 'keno':
                print("Submitting to NEcluster")
                self.build_scale_submission_script(file_name_flag, solve_type)
                self.submit_jobs_to_necluster(file_name_flag)
                self.wait_on_submitted_job(file_name_flag)
            if solve_type == 'tsunami':
                if self.multithreaded_clutch_on_necluster == 'True':
                    print("Solving MT Tsunami")
                    file_name_flag = "mt_tsunami_"
                    ### Solving with MT Tsunami tools
                    mt_tools = MT_Clutch_Tools_v1.MT_Clutch_Tools(template_file="tsunami_template_file.inp",
                                                                  neutrons_per_generation=25000, skip_generations=105)
                    combined_sdf_dict = mt_tools.run_mt_clutch_job(betas=self.proposed_betas,
                                                                   number_of_cases=int(self.number_of_clutch_jobs),
                                                                   file_flag=file_name_flag)
                    ### Pickling this file for later
                    self.combined_sdf_dict = combined_sdf_dict
                    self.write_out_pickle(pickle_file_string=self.sensitivity_dict_mt_tsunami,
                                          write_out_attribute='combined_sdf_dict')
                    file_name_flag = file_name_flag + "0"
                else:
                    print("Submitting to NEcluster")
                    self.build_scale_submission_script(file_name_flag, solve_type)
                    self.submit_jobs_to_necluster(file_name_flag)
                    self.wait_on_submitted_job(file_name_flag)

        ### Get keff
        self.sfh.get_keff_and_uncertainty(file_name_flag + '.out')

        ### Update sensitivites if needed
        if solve_type == 'tsunami':
            if self.multithreaded_clutch_on_necluster == 'True':
                self.sensitivities = combined_sdf_dict
                self.combine_sensitivities_by_list()
            else:
                self.update_sensitivities("tsunami_run_.sdf")

        keff = self.sfh.data_dict[file_name_flag + '.out']['keff']
        return keff

    def build_material_dictionaries(self):
        list_of_material_dictionaries = []
        materials = self.sfh.build_default_material_dicts()
        for material_definition in self.materials:
            ### If it is a mixture of two or more materials:
            if ":" in material_definition:
                mat_dif_split = material_definition.split(":")
                local_material_list = mat_dif_split[0].split("/")
                local_material_ratio = mat_dif_split[1].split("/")

                if len(local_material_list) > 2:
                    print("Unable to combine more than 2 materials into a default material... fix this")
                    exit()

                mat_dict = self.sfh.combine_material_dicts(materials[local_material_list[0]],
                                                           materials[local_material_list[1]],
                                                           int(local_material_ratio[0]))
            else:
                mat_dict = materials[material_definition]

            list_of_material_dictionaries.append(mat_dict)

        return list_of_material_dictionaries

    def build_scale_submission_script(self, file_name_flag, solve_type):
        if solve_type == 'keno':
            script = self.multithreaded_scale_script
        if solve_type == 'tsunami':
            script = self.singlethreaded_scale_script

        script = script.replace('%%%input_flag%%%', file_name_flag)

        scale_script_file = open(file_name_flag + '.sh', 'w')
        scale_script_file.write(script)
        scale_script_file.close()

    def submit_jobs_to_necluster(self, file_name_flag):
        ### Removing any "_done" files, they are how the code knows to continue
        for file in os.listdir("."):
            if "_done" in file:
                os.remove(file)

        ### Submitting current file script
        current_Dir = os.getcwd()
        os.system('ssh -tt necluster.ne.utk.edu "cd ' + current_Dir + ' && qsub ' + file_name_flag + '.sh' + '"')

    def wait_on_submitted_job(self, file_name_flag):
        print("Waiting on job: ", file_name_flag)
        _ = 0
        total_time = 0
        while _ == 0:
            for file in os.listdir("."):
                if '_done' in file:
                    print("Job complete! Continuing...")
                    return

            print("Not yet complete, waiting 15 seconds. Total: ", total_time / 60, "minutes")
            total_time += 15
            time.sleep(15)

    def update_sensitivities(self, sdf_file):
        self.sensitivities = self.sfh.parse_sdf_file_into_dict(sdf_file)
        self.combine_sensitivities_by_list()

    ### This function takes the current tsunami sensitvities (%k/%number dense) and solves for the sensitivity to changes in
    ### caluculates the sensitivity of change to beta
    def calculate_sensitivies(self):
        sensitivities = []
        for mat_count, poison_sensitivity in enumerate(self.poison_sens_list):
            fuelmod_sensitivity = self.fuelmod_sens_list[mat_count]
            beta_ = self.tsunami_betas[mat_count]

            beta_diff = 0.01

            ### Calculating percent change in poison
            x_1_poison_beta_change = (beta_ + beta_diff) / beta_ - 1
            x_1_fuel_mod_beta_change = (1 - beta_ - beta_diff) / (1 - beta_) - 1

            x_2_poison_beta_change = (beta_ - beta_diff) / beta_ - 1
            x_2_fuel_mod_beta_change = (1 - beta_ + beta_diff) / (1 - beta_) - 1

            y_1 = x_1_poison_beta_change * poison_sensitivity + \
                  x_1_fuel_mod_beta_change * fuelmod_sensitivity

            y_2 = x_2_poison_beta_change * poison_sensitivity + \
                  x_2_fuel_mod_beta_change * fuelmod_sensitivity

            x_1 = beta_ + beta_diff
            x_2 = beta_ - beta_diff

            sensitivities.append((y_2 - y_1) / (x_2 - x_1))
        return sensitivities

    ###
    def calculate_sensitivities_2_materials_general(self):
        sensitivities = []
        for mat_count, material_1_sensitivity in enumerate(self.material_1_sensitivities):
            material_2_sensitivity = self.fuelmod_sens_list[mat_count]
            beta_ = self.tsunami_betas[mat_count]

            beta_diff = 0.01

            ### Calculating percent change in poison
            x_1_material_1_beta_change = (beta_ + beta_diff) / beta_ - 1
            x_1_material_2_beta_change = (1 - beta_ - beta_diff) / (1 - beta_) - 1

            x_2_material_1_beta_change = (beta_ - beta_diff) / beta_ - 1
            x_2_material_2_beta_change = (1 - beta_ + beta_diff) / (1 - beta_) - 1

            y_1 = x_1_material_1_beta_change * material_1_sensitivity + \
                  x_1_material_2_beta_change * material_2_sensitivity

            y_2 = x_2_material_1_beta_change * material_1_sensitivity + \
                  x_2_material_2_beta_change * material_2_sensitivity

            x_1 = beta_ + beta_diff
            x_2 = beta_ - beta_diff

            sensitivities.append((y_2 - y_1) / (x_2 - x_1))
        return sensitivities

    ### This function compares proposed changes to self.betas and returns relative
    ### changes
    def get_beta_percent_change(self, proposed_changes):
        ### Beta is defined as: from 0-1.0: 0.10 means 10% material_1,
        ### 90% material_2 as described in materials line in options file
        percent_change_list = []
        for count, beta in enumerate(proposed_changes):
            percent_change_list.append([beta / self.tsunami_betas[count] - 1,
                                        (1 - beta) / (1 - self.tsunami_betas[count]) - 1])

        return percent_change_list

    ### Getting all poison and fuel/mod sensitivities
    ### Returns predicted keff
    def linear_approximation_of_keff(self):
        material_betas_default = self.tsunami_betas
        proposed_betas = self.proposed_betas
        original_keff = float(self.tsunami_keff)
        # print("self.proposed_changes",self.proposed_changes )

        self.combine_sensitivities_by_list()

        expected_delta_k = 0.0
        print(
            "percent_change_in_poison, percent_change_in_fuel_mod, expected_change_psn, expected_change_fm, expected_delta_k")
        for material_count, beta_change in enumerate(proposed_betas):
            percent_change_in_mat_1 = beta_change / material_betas_default[material_count] - 1
            percent_change_in_mat_2 = (1 - beta_change) / (1 - material_betas_default[material_count]) - 1

            expected_change_mat_1 = percent_change_in_mat_1 * self.material_1_sensitivities[material_count] * original_keff
            expected_change_mat_2 = percent_change_in_mat_2 * self.material_2_sensitivities[material_count] * original_keff
            expected_delta_k += expected_change_mat_1 + expected_change_mat_2
            # print(material_count, expected_change_psn, expected_change_fm)
            print(percent_change_in_mat_1, percent_change_in_mat_2, expected_change_mat_1, expected_change_mat_2,
                  expected_delta_k)
        print("linear keff guess", expected_delta_k + original_keff)

        return expected_delta_k + original_keff

### deprecated
    def combine_sensitivities(self):
        # scale_handler = self.sfh
        materials = self.sfh.build_default_material_dicts()
        fuel_mod_material_dict = self.sfh.combine_material_dicts(materials['fuel'], materials['moderator'], 25)
        materials_list = self.build_material_dictionaries()

        material_sens_lists = []
        poison_sens_list = []
        fuelmod_sens_list = []
        for material_loc in self.sensitivities:
            ### Sum all poison and fuel/mod sensitivities
            if material_loc == '0':
                print("SKIPPING TOTAL SENSITIVITY")
                continue
            poison_sum = 0.0
            fuelmod_sum = 0.0
            for isotope in materials['poison']:
                poison_sum += float(self.sensitivities[material_loc][isotope]['sensitivity'])

            for isotope in fuel_mod_material_dict:
                fuelmod_sum += float(self.sensitivities[material_loc][isotope]['sensitivity'])

            poison_sens_list.append(poison_sum)
            fuelmod_sens_list.append(fuelmod_sum)

        self.poison_sens_list = poison_sens_list
        self.fuelmod_sens_list = fuelmod_sens_list

    def combine_sensitivities_by_list(self):
        materials_list = self.build_material_dictionaries()

        material_sens_lists = []
        ### For each material type in the problem location in the problem
        for mat_count, material_dict in enumerate(materials_list, start = 1):
            ### Sum all poison and fuel/mod sensitivities
            sensitivity_sum_list = []
            for material_loc in self.sensitivities:

                if material_loc == '0':
                    print("SKIPPING TOTAL SENSITIVITY")
                    continue

                sum_ = 0.0
                for isotope in material_dict:
                    sum_ += float(self.sensitivities[material_loc][isotope]['sensitivity'])
                sensitivity_sum_list.append(sum_)

            material_sens_lists.append(sensitivity_sum_list)

            setattr(self, "material_" + str(mat_count) + "_sensitivities", sensitivity_sum_list)

    def build_scale_input_from_beta(self, scale_handler,
                                    material_betas,
                                    material_1,
                                    material_2,
                                    template_file_string,
                                    flag,
                                    flag_replacement_string='replace',
                                    temperature=300,
                                    material_count_offset=1,
                                    file_name_flag='default_'):

        material_list = []
        for beta in material_betas:
            material_list.append(scale_handler.combine_material_dicts(material_1, material_2, beta))

        material_string_list = []
        for count, material in enumerate(material_list):
            material_string_list.append(
                scale_handler.build_scale_material_string(material, count + material_count_offset, temperature))

        ### Making list of keys
        flag_list = []
        for x in range(len(material_string_list)):
            flag_list.append(flag.replace(flag_replacement_string, str(x)))

        material_dict = scale_handler.make_data_dict(flag_list, material_string_list)

        scale_handler.create_scale_input_given_target_dict(template_file_string, file_name_flag, material_dict)

    def create_header_string(self, header):
        if header == 'time':
            now = datetime.now()
            return now.strftime("%m/%d/%Y_%H:%M:%S")
        if header.startswith('betas'):
            beta_str = ""
            for beta in self.tsunami_betas:
                beta_str += str(beta) + ","
            return beta_str[:-1]

        if 'proposed_betas' in header:
            beta_str = ""
            for beta in self.proposed_betas:
                beta_str += str(beta) + ","
            return beta_str[:-1]

        if header == 'keff':
            return str(self.keff)

        if header == 'linear_keff':
            return str(self.linear_keff)

        if header == 'tsunami_keff':
            return str(self.tsunami_keff)

        if header == 'solver_type':
            return self.solver_type

        if header == 'keno_keff':
            return str(self.keno_keff)

        if header == 'original_linear_keff':
            return str(self.original_linear_keff)

        if 'material_1_sense' in header:
            sense_str = ""
            for sense in self.material_1_sensitivities:
                sense_str += str(sense) + ","
            return sense_str[:-1]

        if 'material_2_sense' in header:
            sense_str = ""
            for sense in self.material_2_sensitivities:
                sense_str += str(sense) + ","
            return sense_str[:-1]

        if 'beta_sens' in header:
            beta_str = ""
            for beta in self.beta_sensitivities:
                beta_str += str(beta) + ","
            return beta_str[:-1]

        return header + "_FAILED"
