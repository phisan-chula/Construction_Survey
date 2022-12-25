# Construction_Survey

Python script สำหรับช่วยงานประมวลผลงานสำรวจรังวัดเพื่อการก่อสร้าง

ITD_PierSched : สคริปส์อ่านตำแหน่งเสาเข็มในแต่ละตอหม้อ (pier schedule)  

OrangeLine_E1 : งานออกแบบแนวเส้นทางรถไฟในรูปแบบตาราง PDF ที่ส่งมอบให้งานสำรวงวางแนวอ่านขึ้นไปใช้งานในการ setting-out ด้วย GNSS  หรือ TotalStation

Setting_OUT : ซอฟต์แวร์ไลบรารีช่วยการคำนวนผลการอ่านมุมและระยะทางจากกล้อง TotalStation แล้วทำการคำนวนค่าพิกัดที่อ่านได้

UTM Traverse : ซอฟต์แวร์ประมวลผลงานวงรอบที่ใช้ระบบพิกัดยูทีเอ็ม ระบบจะคำนวนเสกลแฟกเตอร์ลดทอนจากระยะทางราบ (chord-on-ellipsoid) ลงไปสู่ระนาบกริดยูทีเอ็ม การปรับแก้วงรอบมีการปรับแก้มุมภายในรูปปิด angular misclosure และใช้กฏเข็มทิศ (compass rule) ในการคำนวนปรับ linear misclousure ระบบยังมีการผลิตแผนที่วงรอบในรูปแบบไฟล์ png, pdf และ svg ให้อีกด้วย ข้อมูลนำเข้าผู้ใช้เขียน Text file ในรูปแบบ "YAML" ดังตัวอย่าง

GeodeticNetwork : ประมวลผลคำนวนปรับแก้โครงข่ายยีออเดติกส์ โดยการรังวัดมุมราบ (ระยะทาง etc) การคำนวนใช้การคำนวนปรับแก้ลีสสแควร์ การประมวลผลคำนวนปรับแก้โครงข่าย เช่น Resection และ Intersection ด้วย GeodeticNetwork จึงทำให้รูปแบบ มึความยืดหยุ่น สามารถกำหนดจุดอ้างอิงได้ไม่จำกัดและรูปแบบการวัดมุมที่เลือกวัดได้อิสระ การกำหนดข้อมูลนำเข้าใช้ฟอร์แมท YAML ค่าสังเกตุมุุมสามารถนำเข้าได้ทั้ง่ในรูปแบบ decimal degree ddd.dddddd และ hexagesimal degree "ddd:mm:ss.s"

RouteSurveying/TraversLR : โปรแกรมคำนวนระยะทางสะสมตามเส้นวงรอบ (linear referencing) พร้อมกับแบ่งระยะทางเป็นระยะคงที่เช่น ทุกๆ 25 เมตร เพื่อกำหนดพิกัดไปใช้ในการรังวัดรูปตัดตามขวางต่อไป

RouteSurveying/CurvePnts : โปรแกรมออกแบบโค้งวงกลมเมื่อกำหนดจุดบนแนวเส้นทางสามจุด คือ จุดก่อนถึง PC (lead-in PC) พิกัดจุด PI และจุดเลยจุด PT ออกไป (leadout PT) ผู้ใช้กำหนดรัศมีดโค้งวงกลมที่ต้องการ และระยะห่างของจุดแบ่งบนโค้งวงกลม ค่าพิกัดบนโค้งบนกลมนี้จะนำไปใช้ในการวางโค้งในสนาม (curve layout) ผลผลิตที่ได้มีรูปแบบ png,pdf,gpck และ TOPCON GTS-7 format สำหรับนำไปโหลดเข้าในกล้องโทเทิ่ลสเตชั่นได้สดวก

![](https://github.com/phisan-chula/Construction_Survey/blob/main/RouteSurveying/CACHE/PLOT_CURVE.png)

usage: python3 CurvePnts.py -a [542939.592,1560557.148],[543219.123,1560612.552],[543408.493,1560534.688] -r 200 -d 20

CurvePnts.py : Generate points on a designated curve from its 3-point alignment Author : Phisan Santitamnont (
phisan.chula@gmail.com ) History 25 Dec 2022 : version 0.1

options:
  -h, --help            show this help message and exit
  -a ALIGN, --align ALIGN
                        3-point of alignment "[E,N],[E,N],[E,N]" for circular curve design
  -r RADIUS, --radius RADIUS
                        design value of the radius in meter
  -d DIVISION, --division DIVISION
                        desired division of the point-on-curve in meter
  -t, -t                annotate text for curve distance at each division
