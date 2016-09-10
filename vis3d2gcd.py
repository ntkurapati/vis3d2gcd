import numpy
import scipy.signal
import os


#patient > trial > left/right

gcd_fields = ("!LeftStrideTime","!LeftCadence","!LeftStepTime","!LeftOppositeFootOff","!LeftOppositeFootContact",
             "!LeftFootOff","!LeftSingleSupport","!LeftDoubleSupport","!LeftStrideLength","!LeftStepLength",
             "!LeftSpeed","!LeftTrunkFlexExt","!LeftTrunkLateralBend","!LeftTrunkRotation","!LeftPelvicTilt",
             "!LeftPelvicObliquity","!LeftPelvicRotation","!LeftHipFlexExt","!LeftHipAbAdduct","!LeftHipRotation",
             "!LeftKneeFlexExt","!LeftKneeValgVar","!LeftKneeRotation","!LeftDorsiPlanFlex","!LeftFootInclination",
             "!LeftFootProgression","!LeftFootRotation","!LeftPelvicAndHipTransverseAngle","!LeftKneeProgression",
             "!LeftLegLengthAsisToFootNorm","!LeftHipFlexExtMoment","!LeftHipAbAdductMoment","!LeftHipRotationMoment",
             "!LeftKneeFlexExtMoment","!LeftKneeValgVarMoment","!LeftKneeRotationMoment","!LeftDorsiPlanFlexMoment",
             "!LeftFootAbAdductMoment","!LeftFootRotationMoment","!LeftHipPower","!LeftHipPowerCoronal",
             "!LeftKneePower","!LeftKneePowerCoronal","!LeftAnklePower","!LeftAnklePowerCoronal")
kinematic_params = ("Pelvic Tilt","Pelvic Obliquity", "Pelvic Rotation", "Hip Flex Ext","Hip Ab Adduct","Hip Rotation",
                    "Knee Flex Ext","Knee Valg Var","Knee Rotation","Dorsi Plan Flex","Foot Rotation","Foot Progression")
mappings = dict()
mappings['Pelvis']=dict()
mappings['Pelvis']['X']="Pelvic Tilt"
mappings['Pelvis']['Y']="Pelvic Obliquity"
mappings['Pelvis']['Z']="Pelvic Rotation"
mappings['Hip']=dict()
mappings['Hip']['X']="Hip Flex Ext"
mappings['Hip']['Y']="Hip Ab Adduct"
mappings['Hip']['Z']="Hip Rotation"
mappings['Knee']=dict()
mappings['Knee']['X']="Knee Flex Ext"
mappings['Knee']['Y']="Knee Valg Var"
mappings['Knee']['Z']="Knee Rotation"
mappings['Ankle']=dict()
mappings['Ankle']['X']="Dorsi Plan Flex"
mappings['Ankle']['Z']="Foot Rotation"
mappings['Foot Progression']=dict()
mappings['Foot Progression']['Z']="Foot Progression"


maindir = "C:\\OI cases _phil_2016\\"

def main():


    subject_dirs = ["060916_%02d" % x for x in range(1, 16)]

    with open('output.csv', 'w') as f:
        f.write(' ')

    subjects = []
    for subject_dir in subject_dirs:
        subject = Subject(subject_id=subject_dir)
        subject.write_to_files(os.path.join(maindir, subject_dir))


class Trial:
    gender = "NotSpecified"
    side = "Left"
    age = 0
    trial_no = 0

    def __init__(self, subject_id, filename, trial_no, side="Unknown"):
        self.subject_id = subject_id
        self.filename = filename
        self.trial_no = trial_no
        self.events = dict()
        self.side = side

        for x in ('LHS', 'RHS', 'LTO', 'RTO'):
            self.events[x] = [-1, -1]
        self.kinematic_data = dict()

    def generate_file_name(self):
        return "_".join("v3d", )

    # Write Data to gcdfile
    def write_to_file(self, target_dir):
        filename = os.path.join(target_dir, "%s_%d.gcd" % (self.side, self.trial_no))
        for side in ("Right", "Left"):
            lines_to_write = ["#!DST-0.1 GCD Elroy Sullivan PhD 1.00"]
            for kinematic_parameter in self.kinematic_data:
                this_data = self.kinematic_data[kinematic_parameter]

                if len(this_data) == 0:
                    break
                this_data = filter_nan(this_data)
                this_data = resample(this_data)
                variable_to_write = self.array_to_gcd(kinematic_parameter, this_data, side=side, dollar=False)
                if variable_to_write:
                    lines_to_write += variable_to_write
            with open(filename, 'w') as gcd_file:
                gcd_file.writelines(lines_to_write)

    def array_to_gcd(self, variable_name, data, side="Left", dollar=False):
        variable_name="".join((side,variable_name) ).replace(" ","")
        if dollar:
            variable_name = "".join(("$", variable_name))
        else:
            variable_name = "".join(("!", variable_name))
        output = [variable_name]
        for datum in data:
            output += ("%.02d" % datum)
        return output

    def __repr__(self):
        return str(self.trial_no)+"_"+str(self.events)




class Subject:

    def __init__(self, subject_id):
        self.trials = dict()
        self.trials["Right"]=dict()
        self.trials["Left"]=dict()

        self.event_file = os.path.join(maindir, subject_id, 'events.txt')
        self.kinematic_file = os.path.join(maindir, subject_id, 'all.txt')

        if os.path.exists(self.event_file):
            event_data_dict = self.load_event_data()
        if os.path.exists(self.kinematic_file):
            self.load_kinematic_data()
        else:
            print("MISSING:", self.kinematic_file)

    def load_event_data(self):
        #print(self.event_file)
        event_data_file = numpy.loadtxt(
            self.event_file, skiprows=2,
            dtype={'names': ('file', 'folder', 'event_name', 'item', 'time'),
                   'formats': ('S51', 'S10',  'S3', 'i2', 'f8')})

        # Replace ditto rows "-" with their actual values
        for event1, event2 in zip(event_data_file[:-1], event_data_file[1:]):
            if event2[0] == b'-':
                for i in range(0, 3):
                    event2[i] = event1[i]

        #print(event_data_file)

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
            value = int(round(row[4]*120, 0))
            self.trials["Right"][trial_no].events[row[2].decode()][int(row[3])-1] = value
            self.trials["Left"][trial_no].events[row[2].decode()][int(row[3]) - 1] = value

    # Load kinematic data from Visual 3D output file
    def load_kinematic_data(self):
        header_labels = numpy.genfromtxt(self.kinematic_file, delimiter='\t')[5:]

        #process data headers
        file_data = tuple(open(self.kinematic_file, 'r'))
        data_header_files = file_data[0].strip("\n").split('\t')
        data_header_labels = file_data[1].strip("\n").split('\t')
        data_header_xyz = file_data[4].strip("\n").split('\t')
        data_headers = zip(data_header_labels, data_header_xyz, data_header_files, range(0, len(data_header_labels)))
        orgdata = dict()
        next(data_headers)
        with open('output.csv', 'a') as input_file:
            for (header_label, header_xyz, header_file, colnum) in data_headers:
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
                header_name = mappings[header_label][header_xyz]

                # Extract the column of values
                this_data = header_labels[:, colnum]
                # print(this_data)

                self.trials[side][trial_num].kinematic_data[header_name] = this_data
                this_data = filter_nan(this_data)

                print(filename, subj_id, trial_num, side, header_name, numpy.max(this_data), numpy.min(this_data),
                     numpy.mean(this_data), sep='\t')

                toprint = ",".join((filename, subj_id, str(trial_num), side, header_name, str(numpy.nanmax(this_data)), str(numpy.nanmin(this_data)),
                      str(numpy.nanmean(this_data))))

                input_file.write(toprint)
                input_file.write('\n')

    def write_to_files(self, target_dir):
        for side in ("Right", "Left"):
            #print(self.trials[side])
            for key in self.trials[side]:
                self.trials[side][key].write_to_file(target_dir)


mappings = dict()
mappings['Pelvis']=dict()
mappings['Pelvis']['X']="Pelvic Tilt"
mappings['Pelvis']['Y']="Pelvic Obliquity"
mappings['Pelvis']['Z']="Pelvic Rotation"
mappings['Hip']=dict()
mappings['Hip']['X']="Hip Flex Ext"
mappings['Hip']['Y']="Hip Ab Adduct"
mappings['Hip']['Z']="Hip Rotation"
mappings['Knee']=dict()
mappings['Knee']['X']="Knee Flex Ext"
mappings['Knee']['Y']="Knee Valg Var"
mappings['Knee']['Z']="Knee Rotation"
mappings['Ankle']=dict()
mappings['Ankle']['X']="Dorsi Plan Flex"
mappings['Ankle']['Z']="Foot Rotation"
mappings['Foot Progression']=dict()
mappings['Foot Progression']['Z']="Foot Progression"



def filter_nan(x):
    x = x[numpy.logical_not(numpy.isnan(x))]
    return x

def resample(x):
    if len(x) > 0:
        x = scipy.signal.resample(x, 50)
    return x

main()



#load_kinematic_data(filenr)



"""
pelvic tilt = pelvis x
hip flex/ext = hip x
knee flex/ext = knee x
ankle flex/ext = ankle x


pelvic obliquity = pelvis y
hip ab/ad = hip y
knee varus = knee y
foot progression = foot progression z

pelvis rotation = pelvis z
hip rotation = hip z
tib rotation = knee z
foot rotation = ankle z

LeftPelvis	LeftPelvis	LeftPelvis	LeftHip	Left Hip	Left Hip	Left Knee	Left Knee	Left Knee	Left Ankle	Left Ankle	Left Foot Progression
Pelvic Tilt	Pelvic Obliquity	Pelvic Rotation	Hip Flex Ext	Hip Ab Adduct	Hip Rotation	Knee Flex Ext	Knee Valg Var	Knee Rotation	Dorsi Plan Flex	Foot Rotation	Foot Progression
"""
