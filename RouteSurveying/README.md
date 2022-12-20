Route surveying is a type of surveying that is used to determine the location of a route 
or corridor for a road, railway, pipeline, or other linear infrastructure. 
It involves the measurement of distances, angles, and elevations along the route, 
as well as the determination of the route's alignment. Route surveying is used to ensure that 
the route is safe, efficient, and cost-effective.

  A program 'TraversLR.py' will assist route surveying task by reading CSV of designated
traverse stations and then generate two linear referencing list of points namely 
1) TravDIVISION.csv list of fixed-length division point of "kilometer station: KM"
2) TravSTATION.csv list of points composing a traverse which is closely deifned the
   coming designed route alignment.
3) GIS file of those surveying components.

Example of designated traverse stations 

| Sta  | EPSG  | E          | N           | H       | dist_m   | PSF       |
| ---- | ----- | ---------- | ----------- | ------- | -------- | --------- |
| P-01 | 32647 | 542694.651 | 1560574.888 | 999.999 | 0.000    | 1.0061383 |
| P-02 | 32647 | 542898.406 | 1560557.387 | 999.999 | 204.505  | 1.0061383 |
| P-03 | 32647 | 543217.633 | 1560618.695 | 999.999 | 529.566  | 1.0061382 |
| P-04 | 32647 | 543463.560 | 1560501.273 | 999.999 | 802.088  | 1.0061383 |
| P-05 | 32647 | 543570.300 | 1560408.985 | 999.999 | 943.192  | 1.0061384 |
| P-06 | 32647 | 543819.493 | 1560282.785 | 999.999 | 1222.519 | 1.0061385 |

