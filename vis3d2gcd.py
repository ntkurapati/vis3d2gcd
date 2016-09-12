import numpy
import scipy.signal
import os
import glob

"""
The MIT License (MIT)

Copyright (c) 2016 Orthopedic and Rehabilitation Engineering Center, Medical College of Wisconsin and Marquette University

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.


Requirements:
Python 3.5, numpy and scipy. (Free to use)
I recommend Anaconda (https://www.continuum.io/downloads) which includes all three packages.

Install Anaconda
Download this program from github, and run this script with python.

Instructions for each patient:
Open Visual 3D CMO File
Go to "Signals and Events" tab
Click "EVENT_LABEL"
Click "Export ASCII", save as "events.txt"
Close

Click Pipeline Menu
Click "Open Pipeline"
Point to the "data_export.v3s" that is included with this program
Click "Export_Data_to_ASCII_File"
Change filename to "all.txt" in the patient's data folder.
Execute Pipeline
Run this script

"""


VIS3D_DATA_DIR = "C:\\OI cases _phil_2016\\"  # Where to find Visual3D data
PATTERN = "060916*"  # Pattern for subject folders
PATIENT_DATABASE = "C:\\patient_database2\\Patients\\"  # folder for PatientsAndServices Database
EVENTS_FILE = 'events.txt'  # file for events from visual3D
V3D_EXPORT_FILE = 'all.txt'
ENCOUNTER_DATE = "6-9-16"
EVENT_TYPES = ('LHS', 'RHS', 'LTO', 'RTO')
TIME_SCALING = 120
DATA_STYLE = "Manila"

kinematic_params = ("Pelvic Tilt","Pelvic Obliquity", "Pelvic Rotation", "Hip Flex Ext","Hip Ab Adduct","Hip Rotation",
                    "Knee Flex Ext","Knee Valg Var","Knee Rotation","Dorsi Plan Flex","Foot Rotation","Foot Progression")

header_mappings = {'Ankle':            {'X': 'Dorsi Plan Flex', 'Z': 'Foot Rotation'},
                   'Hip':              {'X': 'Hip Flex Ext',       'Z': 'Hip Rotation',    'Y': 'Hip Ab Adduct'},
                   'Pelvis':           {'X': 'Pelvic Tilt',        'Z': 'Pelvic Rotation', 'Y': 'Pelvic Obliquity'},
                   'Knee':             {'X': 'Knee Flex Ext',      'Z': 'Knee Rotation',   'Y': 'Knee Valg Var'},
                   'Foot Progression': {'Z': 'Foot Progression'}}

def main():
    # clear output file
    with open('output.csv', 'w') as f:
        f.write(' ')

    # Iterate through subject directories to import data
    subject_dirs = glob.glob(os.path.join(VIS3D_DATA_DIR,PATTERN))
    subjects = []
    for subject_dir_full in subject_dirs:
        subject_dir = subject_dir_full.split("\\")[-1]
        subject = Subject(subject_id=subject_dir)

        # Custom to Manila data - convert subject id to database MRN
        if DATA_STYLE == "Manila":
            db_subj_dir = subject_dir.replace("_", "").lstrip("0")

        # Export gcd files
        subject.write_to_files(os.path.join(PATIENT_DATABASE, db_subj_dir, ENCOUNTER_DATE))


class Trial:
    def __init__(self, subject_id, filename, trial_no, side="Unknown", gender="NotSpecified"):
        self.subject_id = subject_id
        self.gender = gender
        self.filename = filename
        self.trial_no = trial_no
        self.events = dict()
        self.side = side

        for x in EVENT_TYPES:
            self.events[x] = [-1, -1]
        self.kinematic_data = dict()

    def generate_file_name(self):
        return "v3d_Barefoot%d_%s_%s_6-9-16.gcd" % (self.trial_no, self.side, self.subject_id)

    # Write Data to gcdfile
    def gcd_export(self, target_dir):
        filename = os.path.join(target_dir, self.generate_file_name())

        lines_to_write = ["#!DST-0.1 GCD Elroy Sullivan PhD 1.00\n"]

        # Need to implement these
        """"!LeftStrideTime","!LeftCadence","!LeftStepTime","!LeftOppositeFootOff","!LeftOppositeFootContact",
             "!LeftFootOff","!LeftSingleSupport","!LeftDoubleSupport","!LeftStrideLength","!LeftStepLength","""

        # Calculate stride time, etc.
        if self.side == "Right" and -1 not in self.events["RHS"]:
            #hs_frame1 = int(round(self.events["RHS"][0]*TIME_SCALING, 0))
            #hs_frame2 = int(round(self.events["RHS"][1]*TIME_SCALING, 0))

            stride_time = self.events["RHS"][1]-self.events["RHS"][0]
            cadence = 60.0/(stride_time)
            lines_to_write += array_to_gcd_format("StrideTime", stride_time, variable_type="num", side=self.side)
            lines_to_write += array_to_gcd_format("Cadence", cadence, variable_type="num", side=self.side)
        if self.side == "Left" and -1 not in self.events["LHS"]:
            stride_time = self.events["LHS"][1]-self.events["LHS"][0]
            cadence = 60.0/(stride_time)
            lines_to_write += array_to_gcd_format("StrideTime", stride_time, variable_type="num", side=self.side)
            lines_to_write += array_to_gcd_format("Cadence", cadence, variable_type="num", side=self.side)

        # keep track of kinematics available
        kinematics_added = 0
        for kinematic_parameter in self.kinematic_data:

            this_data = self.kinematic_data[kinematic_parameter]

            # Don't bother if empty data
            if len(this_data) == 0:
                break
            kinematics_added += 1

            # re-sample the data to 51 points
            this_data = resample_to_51(this_data)

            # convert to gcd format
            variable_to_write = array_to_gcd_format(kinematic_parameter, this_data, variable_type="array",
                                                    side=self.side, prefix="!")
            if variable_to_write:
                lines_to_write += variable_to_write

        # Write to file if there are kinematics
        if kinematics_added:
            with open(filename, 'w') as gcd_file:
                gcd_file.writelines(lines_to_write)


# Formats variables/lists into the gcd format
def array_to_gcd_format(variable_name, data, variable_type="str", side="Unknown", prefix="!"):
    variable_name = "".join((prefix, side, variable_name)).replace(" ", "")
    output = [variable_name, "\n"]
    if variable_type == "array":
        for datum in data:
            output += ("%f\n" % datum)
    elif variable_type == "str":
        output += ("%s\n" % data)
    elif variable_type == "num":
        output += ("%f\n" % data)
    return output


class Subject:
    def __init__(self, subject_id):
        # Initialize trials
        self.trials = dict()
        self.trials["Right"] = dict()
        self.trials["Left"] = dict()

        # find kinematic file
        self.event_file = os.path.join(VIS3D_DATA_DIR, subject_id, EVENTS_FILE)
        self.kinematic_file = os.path.join(VIS3D_DATA_DIR, subject_id, V3D_EXPORT_FILE)

        # Check if paths exist
        if os.path.exists(self.event_file):
            self.load_event_data()
        if os.path.exists(self.kinematic_file):
            self.load_kinematic_data()
        else:
            print("MISSING:", self.kinematic_file)

    # Load event data
    def load_event_data(self):
        event_data_file = numpy.loadtxt(
            self.event_file, skiprows=2,
            dtype={'names': ('file', 'folder', 'event_name', 'item', 'time'),
                   'formats': ('S51', 'S10',  'S3', 'i2', 'f8')})

        # Replace ditto rows "-" with their actual values
        for event1, event2 in zip(event_data_file[:-1], event_data_file[1:]):
            if event2[0] == b'-':
                for i in range(0, 3):
                    event2[i] = event1[i]

        # read in the rows of the visual3d export ascii files
        for row in event_data_file:
            filename_parts = row[0].decode().strip('\'').replace('.c3d', '').split("_")
            subject_id = "_".join((filename_parts[0], filename_parts[1]))
            trial_no = int(filename_parts[4])
            print(trial_no, row)
            if trial_no not in self.trials["Right"]:
                self.trials["Right"][trial_no] = Trial(subject_id, self.event_file, trial_no, side="Right")
                self.trials["Left"][trial_no] = Trial(subject_id, self.event_file, trial_no, side="Left")
                print('created trial')
            value = row[4]
            self.trials["Right"][trial_no].events[row[2].decode()][int(row[3]) - 1] = value
            self.trials["Left"][trial_no].events[row[2].decode()][int(row[3]) - 1] = value

    # Load kinematic data from Visual 3D output file
    def load_kinematic_data(self):
        vis3d_file_data = numpy.genfromtxt(self.kinematic_file, delimiter='\t')[5:]

        # Process data files
        file_data = tuple(open(self.kinematic_file, 'r'))

        data_header_files = file_data[0].strip("\n").split('\t')       # File name row
        data_header_labels = file_data[1].strip("\n").split('\t')  # Data Label row
        data_header_xyz = file_data[4].strip("\n").split('\t')  # Axis row
        # Zip these together for iteration
        data_headers = zip(data_header_labels, data_header_xyz, data_header_files, range(0, len(data_header_labels)))

        # Skip first column
        next(data_headers)
        output_lines = []

        # go through each column of the vis3d export file, import into a Trial
        for (header_label, header_xyz, header_file, col_num) in data_headers:

            # Parse Subject ID
            filename = header_file.split("\\")[-1]
            trial_num = int(filename.split('_')[-1].replace('.c3d', ''))
            subj_id = "_".join(filename.split('_')[0:2])

            # Handle Left/Right
            side = "Unknown"
            if "Left" in header_label:
                side = "Left"
                header_label = header_label.replace("Left", "").strip(' ')
            if "Right" in header_label:
                side = "Right"
                header_label = header_label.replace("Right", "").strip(' ')

            # What Kinematic parameter is this column?
            header_name = header_mappings[header_label][header_xyz]

            # Extract the column of values
            column_data = vis3d_file_data[:, col_num]

            # Filter out non-numeric values
            column_data = filter_nan(column_data)

            # If there's a column left, assign to the trial
            if len(column_data):
                self.trials[side][trial_num].kinematic_data[header_name] = column_data
                print(filename, subj_id, trial_num, side, header_name, numpy.max(column_data), numpy.min(column_data),
                      numpy.mean(column_data), sep='\t')
                # Record stats for output file
                output_lines += ",".join((filename, subj_id, str(trial_num), side, header_name,
                                          str(numpy.nanmax(column_data)), str(numpy.nanmin(column_data)),
                                          str(numpy.nanmean(column_data))))

        # Write stats to file
        with open('output.csv', 'a') as output_file:
            for to_print in output_lines:
                output_file.write(to_print)
                output_file.write('\n')

    # Write gcd files
    def write_to_files(self, target_dir):
        for side in ("Right", "Left"):
            for header in self.trials[side]:
                if any(self.trials[side][header].events):
                    self.trials[side][header].gcd_export(target_dir)


# Filters out non-numeric data
def filter_nan(x):
    x = x[numpy.logical_not(numpy.isnan(x))]
    return x


# Resamples data to 51 data points
def resample_to_51(x):
    if len(x) > 0:
        x = scipy.signal.resample(x, 51)
    return x

main()


