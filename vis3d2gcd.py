import numpy
import scipy.signal
import os

kinematic_params = ("Pelvic Tilt","Pelvic Obliquity", "Pelvic Rotation", "Hip Flex Ext","Hip Ab Adduct","Hip Rotation",
                    "Knee Flex Ext","Knee Valg Var","Knee Rotation","Dorsi Plan Flex","Foot Rotation","Foot Progression")

header_mappings = {'Ankle':            {'X': 'Dorsi Plan Flex', 'Z': 'Foot Rotation'},
            'Hip':              {'X': 'Hip Flex Ext',       'Z': 'Hip Rotation',    'Y': 'Hip Ab Adduct'},
            'Pelvis':           {'X': 'Pelvic Tilt',        'Z': 'Pelvic Rotation', 'Y': 'Pelvic Obliquity'},
            'Knee':             {'X': 'Knee Flex Ext',      'Z': 'Knee Rotation',   'Y': 'Knee Valg Var'},
            'Foot Progression': {'Z': 'Foot Progression'}}

VIS3D_DATA_DIR = "C:\\OI cases _phil_2016\\"
EVENTS_FILE = 'events.txt'
V3D_EXPORT_FILE = 'all.txt'
EVENT_TYPES = ('LHS', 'RHS', 'LTO', 'RTO')
TIME_SCALING = 120


def main():
    # clear output file
    with open('output.csv', 'w') as f:
        f.write(' ')

    # Iterate through subject directory
    subject_dirs = ["060916_%02d" % x for x in range(1, 16)]
    subjects = []
    for subject_dir in subject_dirs:
        subject = Subject(subject_id=subject_dir)
        subject.write_to_files(os.path.join(VIS3D_DATA_DIR, subject_dir))


class Trial:
    gender = "NotSpecified"

    def __init__(self, subject_id, filename, trial_no, side="Unknown"):
        self.subject_id = subject_id
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
    def write_to_file(self, target_dir):
        filename = os.path.join(target_dir, self.generate_file_name())
        print(filename, self.side)

        lines_to_write = ["#!DST-0.1 GCD Elroy Sullivan PhD 1.00\n"]

        # keep track of kinematics available
        kinematics_added = 0
        for kinematic_parameter in self.kinematic_data:

            this_data = self.kinematic_data[kinematic_parameter]

            # Don't bother if empty data
            if len(this_data) == 0:
                break
            kinematics_added += 1

            # resample the data to 51 points
            this_data = resample(this_data)

            # convert to gcd format
            variable_to_write = Trial.array_to_gcd(kinematic_parameter, this_data, side=self.side, prefix="!")
            if variable_to_write:
                lines_to_write += variable_to_write

        # Write to file if there are kinematics
        if kinematics_added:
            with open(filename, 'w') as gcd_file:
                gcd_file.writelines(lines_to_write)

    # Formats variables/lists into the gcd format
    def array_to_gcd(variable_name, data, variable_type="str", side="Unknown", prefix="!"):
        variable_name = "".join((prefix, side, variable_name)).replace(" ", "")
        print(variable_name)
        output = [variable_name, "\n"]
        for datum in data:
            output += ("%f\n" % datum)
        return output


class Subject:
    def __init__(self, subject_id):
        # Initialize trials
        self.trials = dict()
        self.trials["Right"] = dict()
        self.trials["Left"] = dict()

        # kinematic file
        self.event_file = os.path.join(VIS3D_DATA_DIR, subject_id, EVENTS_FILE)
        self.kinematic_file = os.path.join(VIS3D_DATA_DIR, subject_id, V3D_EXPORT_FILE)

        if os.path.exists(self.event_file):
            event_data_dict = self.load_event_data()
        if os.path.exists(self.kinematic_file):
            self.load_kinematic_data()
        else:
            print("MISSING:", self.kinematic_file)

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

        # read in the rows of the evt files
        for row in event_data_file:
            filename_parts = row[0].decode().strip('\'').replace('.c3d', '').split("_")
            subject_id = "_".join((filename_parts[0], filename_parts[1]))
            trial_no = int(filename_parts[4])
            print(trial_no, row)
            if trial_no not in self.trials["Right"]:
                self.trials["Right"][trial_no] = Trial(subject_id, self.event_file, trial_no, side="Right")
                self.trials["Left"][trial_no] = Trial(subject_id, self.event_file, trial_no, side="Left")
                print('created trial')
            #timestamp to frame number
            value = int(round(row[4]*TIME_SCALING, 0))
            self.trials["Right"][trial_no].events[row[2].decode()][int(row[3]) - 1] = value
            self.trials["Left"][trial_no].events[row[2].decode()][int(row[3]) - 1] = value

    # Load kinematic data from Visual 3D output file
    def load_kinematic_data(self):
        header_labels = numpy.genfromtxt(self.kinematic_file, delimiter='\t')[5:]

        # Process data files
        file_data = tuple(open(self.kinematic_file, 'r'))
        data_header_files = file_data[0].strip("\n").split('\t')
        data_header_labels = file_data[1].strip("\n").split('\t')
        data_header_xyz = file_data[4].strip("\n").split('\t')
        data_headers = zip(data_header_labels, data_header_xyz, data_header_files, range(0, len(data_header_labels)))

        # Skip first column
        next(data_headers)
        output_lines = []

        for (header_label, header_xyz, header_file, col_num) in data_headers:
            filename = header_file.split("\\")[-1]
            trial_num = int(filename.split('_')[-1].replace('.c3d', ''))
            subj_id = "_".join(filename.split('_')[0:2])
            side = "Unknown"
            if "Left" in header_label:
                side = "Left"
                header_label = header_label.replace("Left", "").strip(' ')
            if "Right" in header_label:
                side = "Right"
                header_label = header_label.replace("Right", "").strip(' ')
            header_name = header_mappings[header_label][header_xyz]

            # Extract the column of values
            this_data = header_labels[:, col_num]
            # print(this_data)

            this_data = filter_nan(this_data)
            if len(this_data):
                self.trials[side][trial_num].kinematic_data[header_name] = this_data
                print(filename, subj_id, trial_num, side, header_name, numpy.max(this_data), numpy.min(this_data),
                     numpy.mean(this_data), sep='\t')

                output_lines += ",".join((filename, subj_id, str(trial_num), side, header_name, str(numpy.nanmax(this_data)), str(numpy.nanmin(this_data)),
                      str(numpy.nanmean(this_data))))
        with open('output.csv', 'a') as output_file:
            for toprint in output_lines:
                output_file.write(toprint)
                output_file.write('\n')

    #Write gcd files
    def write_to_files(self, target_dir):
        for side in ("Right", "Left"):
            for header in self.trials[side]:
                if any(self.trials[side][header].events):
                    self.trials[side][header].write_to_file(target_dir)


def filter_nan(x):
    x = x[numpy.logical_not(numpy.isnan(x))]
    return x


def resample(x):
    if len(x) > 0:
        x = scipy.signal.resample(x, 51)
    return x

main()


