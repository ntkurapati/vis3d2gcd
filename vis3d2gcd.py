import numpy
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



def load_event_data(filee):
    eventdata = numpy.loadtxt(filee, skiprows=2, dtype={'names': ('file', 'folder', 'event_name', 'item', 'time'),
                                            'formats': ('S51', 'S10',  'S3', 'i2','f8' )})

    for index, event in enumerate(eventdata):
        #print(event[0])
        if event[0]==b'-':
            for i in range(0,3):
                eventdata[index][i] = eventdata[index-1][i]
    event_data_dict = dict()
    for row in eventdata:
        #print(row)
        if row[0] not in event_data_dict:
            event_data_dict[row[0]]= dict()
        if row[2] not in event_data_dict[row[0]]:
            event_data_dict[row[0]][row[2]]= [-1,-1]
        event_data_dict[row[0]][row[2]][int(row[3])-1]= int(round( row[4]*120,0))

    #print(event_data_dict)
    return event_data_dict

def load_kinematic_data(input_file):
    data = numpy.genfromtxt(input_file, delimiter='\t')[5:]

    file_data = tuple(open(input_file, 'r'))
    data_header_files = file_data[0].strip("\n").split('\t')
    data_header_labels = file_data[1].strip("\n").split('\t')
    data_header_xyz = file_data[4].strip("\n").split('\t')
    data_headers = zip(data_header_labels, data_header_xyz, data_header_files, range(0, len(data_header_labels)))
    orgdata = dict()
    with open('output.csv', 'a') as f:
        for (header_label, header_xyz, header_file, colnum) in data_headers:
            if colnum == 0:
                continue
            filename = header_file.split("\\")[-1]
            trial_num = int(filename.split('_')[-1].replace('.c3d', ''))
            id = "_".join(filename.split('_')[0:2])
            side = "Unknown"
            if "Left" in header_label:
                side = "L"
                header_label = header_label.replace("Left", "").strip(' ')
            if "Right" in header_label:
                side = "R"
                header_label = header_label.replace("Right", "").strip(' ')


            header_name = mappings[header_label][header_xyz]
            this_data = data[:, colnum]
            # print(this_data)
            orgdata[header_name] = this_data
            #print(filename, id, trial_num, side, header_name, numpy.nanmax(this_data), numpy.nanmin(this_data),
             #     numpy.nanmean(this_data), sep='\t')

            toprint= ",".join((filename, id, str(trial_num), side, header_name, str(numpy.nanmax(this_data)), str(numpy.nanmin(this_data)),
                  str(numpy.nanmean(this_data))))

            f.write(toprint)
            f.write('\n')


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

subjects = ["060916_%02d" % x for x in range(1,16)]

with open('output.csv', 'w') as f:
    f.write(' ')


for subject in subjects:
    event_file = os.path.join(maindir, subject, 'events.txt')
    kinematic_file = os.path.join(maindir, subject, 'all.txt')
    if os.path.exists(event_file):
        event_data_dict = load_event_data(event_file)
    if os.path.exists(kinematic_file):
        load_kinematic_data(kinematic_file)
    else:
        print("MISSING:", kinematic_file)

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
