# Foundation Computation Program Rev.01
import numpy as np 
import csv 

################################## Function List ##################################

# Convert Angle : แปลงมุม (Credit Prajuab Riabroy's Blog)
PI = np.pi
DEG2RAD = PI / 180.0
RAD2DEG= 180.0 / PI

# แปลง degree > deg,min,sec (Credit Prajuab Riabroy's Blog)
def deg2dms(dd):
  sign=1
  if (dd < 0):
    sign = -1
  dd=abs(dd)
  minutes, seconds = divmod(dd*3600,60)
  degrees, minutes = divmod(minutes,60)
  return (sign, degrees, minutes, seconds)

# แปลง deg,min,sec > deg - min - sec (Credit Prajuab Riabroy's Blog)
def DMS2str(degree, minute, second, numdec):
  degree = abs(degree); minute = abs(minute); second = abs(second)
  s ='{:.%df}' % numdec
  ss = s.format(second)
  smin = s.format(60.0)
  mm ='{:.0f}'.format(minute)
  if (ss == smin):
    minute += 1
    ss = s.format(0.0)
    if (minute >= 60):
      mm = '0'
      degree += 1
    else:
      mm ='{:.0f}'.format(minute)
  return '{:.0f}'.format(degree)+"-"+mm+"-"+ss

# Write csv file : เขียนข้อมูลลงไฟล์ csv
def WriteCSV (export_pile_schedule_result):
  # 'a' is append, newline='' ขึ้นบรรทัดใหม่, encoding='utf-8'  อักขระทุกอย่างของ Unicode นำมาใช้หมด
	with open ('export_pile_schedule_result.csv', 'a', newline='', encoding='utf-8') as file:
		#fw is file writer
		fw = csv.writer(file)
		fw.writerow(export_pile_schedule_result)

# Foudation Position : คำนวณตำแหน่งเสาเข็ม/มุมฐานราก
def Foudation_Position(Ncenter, Ecenter,  Azimuth, Chainage, Offset):
	Ni = Ncenter + Chainage * np.cos(Azimuth * DEG2RAD) + Offset * np.cos((Azimuth + 90) * DEG2RAD)
	Ei = Ecenter + Chainage * np.sin(Azimuth * DEG2RAD) + Offset * np.sin((Azimuth + 90) * DEG2RAD)
	return Ni, Ei

############################# Pile Schedule Calculation ############################

# นำเข้าข้อมูล Pier Schedule.csv (ประเภทข้อความ)                 
PierSC = np.loadtxt('01_Pier_Schedule.csv', delimiter=',', skiprows=1, dtype=str)

# นำเข้าข้อมูล Chinage&Offset Axis.csv (ประเภทข้อความ)
CHOS_Axis = np.loadtxt('02_CH&OS_Axis.csv', delimiter=',', skiprows=1, dtype=str)

# ตั้งชื่อหัวตารางและเขียนลงใน CSV (Export)
Head_Column = ['Point', 'N', 'E', 'Pier No', 'Sta', 'Pier Az', 'F Type']
WriteCSV(Head_Column)

# นับจำนวณข้อมูลที่อยู่ใน PierSC Array
count_array1 = len(PierSC)

# กำหนดชื่อข้อมูลตาม Column ใน PierSC Array
for i in range(count_array1):
  Pier_No = PierSC[i][0] #Column 1 is Pier No. (ประเภทข้อความ)
  Sta = float(PierSC[i][1]) #Column 2 is Station (ประเภทตัวเลข)
  Nc = float(PierSC[i][2]) #Column 3 is Northing (ประเภทตัวเลข
  Ec = float(PierSC[i][3]) #Column 4 is Easting (ประเภทตัวเลข
  Pier_Az = float(PierSC[i][4]) #Column 5 is Pier Azimuth (ประเภทตัวเลข
  FSkew = float(PierSC[i][5]) #Column 6 is Footing Skew (ประเภทตัวเลข)
  Found_Type1 = PierSC[i][6] #Column 7 is Foundation Type (ประเภทข้อความ)

  # แปลง Pier Azimuth Deg>DMS
  sn, d, m, s = deg2dms(Pier_Az)
  Pier_AzDMS = DMS2str(d, m, s, 2) # (ประเภทข้อความ)

  # ตรวจสอบ Foundation type ใน PierSC Array
  if Found_Type1 == 'N/A':
    continue # ข้ามข้อมูลในกรณีไม่มี Foundation type
  else:
    # นับจำนวณข้อมูลที่อยู่ใน CHOS_Axis Array
    count_array2 = len(CHOS_Axis)

    # กำหนดชื่อข้อมูล Column ของ Foundation type ใน CHOS_Axis Array
    for j in range(count_array2):
        Found_Type2 = CHOS_Axis[j][0]

        # ตรวจสอบ Foundation type ทั้ง 2 Array
        if Found_Type1 != Found_Type2:
            continue # ข้ามข้อมูลในกรณี Foundation type ไม่ตรงกัน
        else:
            # กรณี Foundation type ตรงกัน
            print('{}, N: {:.3f} E: {:.3f}, {}, Sta: {:.3f}, Az: {}, {}'.format('CL', Nc, Ec, Pier_No, Sta, Pier_AzDMS, Found_Type1))

            # เขียนข้อมูล Pier Center ลง CSV file (Export)
            Result_1 = ['CL', Nc, Ec, Pier_No, Sta, Pier_AzDMS, Found_Type1]
            WriteCSV(Result_1)

            for k in range(1,30,3): # range(Start, End, Step), 1 คือ Column ที่ 1, 30 คือ Column ที่ 30, 3 : คือ นับเลขที่ละ 3 เช่น 0, 2, 5, 8 .......
                # หาตัวเลขคู่อันดับ เพื่อดึ่งข้อมูลใน CHOS_Axis Array
                Index_P = k # ประเภทข้อความ
                Index_Ch = Index_P + 1 # ประเภทข้อความ
                Index_Os = Index_Ch + 1 # ประเภทข้อความ
                Final_Az = Pier_Az + FSkew # ประเภทตัวเลข

                # ตรวจสอบเสาเข็มของ Foundation type
                if CHOS_Axis[j][Index_Ch] and CHOS_Axis[j][Index_Ch] == 'N/A':
                    continue # ข้ามข้อมูลเสาเข็มหรือข้อมูลมุมฐานราก ในกรณีไม่มีค่า Chainage / Offset Axis
                else:
                  P = Pier_No + '/' + CHOS_Axis[j][Index_P] # ประเภทข้อความ
                  Ch = float(CHOS_Axis[j][Index_Ch]) # ประเภทตัวเลข
                  Os = float(CHOS_Axis[j][Index_Os]) # ประเภทตัวเลข

                  # คำนวณหาตำแหน่งเสาเข็มหรือมุมฐานราก แต่ละ Foundation type
                  Pile_Pos = Foudation_Position(Nc, Ec, Final_Az, Ch, Os) 
                  print('{} N: {:.3f} E: {:.3f}'.format(P, Pile_Pos[0], Pile_Pos[1]))

                  # เขียนข้อมูลตำแหน่งเสาเข็มหรือมุมฐานรากลงใน CSV file (Export)
                  Result_2 = [P, Pile_Pos[0], Pile_Pos[1]]
                  WriteCSV(Result_2)
